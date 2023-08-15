# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Datacite to DCAT serializer."""
import mimetypes

from datacite import schema43
from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import SimpleSerializer
from lxml import etree as ET
from pkg_resources import resource_stream
from werkzeug.utils import cached_property

from invenio_rdm_records.contrib.journal.processors import JournalDataciteDumper
from invenio_rdm_records.resources.serializers.dcat.schema import DcatSchema


class DCATSerializer(MarshmallowSerializer):
    """DCAT serializer for records."""

    def __init__(self, **options):
        """Constructor."""
        super().__init__(
            format_serializer_cls=SimpleSerializer,
            object_schema_cls=DcatSchema,
            list_schema_cls=BaseListSchema,
            schema_kwargs={"dumpers": [JournalDataciteDumper()]},  # Order matters
            encoder=self._etree_tostring,
            **options,
        )

    def _etree_tostring(self, record, **kwargs):
        root = self.transform_with_xslt(record, **kwargs)
        return ET.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        ).decode("utf-8")

    @cached_property
    def xslt_transform_func(self):
        """Return the DCAT XSLT transformation function."""
        with resource_stream(
            "invenio_rdm_records.resources.serializers", "dcat/datacite-to-dcat-ap.xsl"
        ) as f:
            xsl = ET.XML(f.read())
        transform = ET.XSLT(xsl)
        return transform

    def _add_files(self, root, files):
        """Add files information via distribution elements."""
        ns = root.nsmap

        def download_url(file):
            url = file.get("download_url")
            return {"{{{rdf}}}resource".format(**ns): url} if url else None

        def media_type(file):
            return mimetypes.guess_type(file["key"])[0]

        def byte_size(file):
            return str(file["size"]) if file.get("size") else None

        def access_url(file):
            url = file.get("access_url")
            return {"{{{rdf}}}resource".format(**ns): url} if url else None

        files_fields = {
            "{{{dcat}}}downloadURL": download_url,
            "{{{dcat}}}mediaType": media_type,
            "{{{dcat}}}byteSize": byte_size,
            "{{{dcat}}}accessURL": access_url,
            # TODO: there's also "spdx:checksum", but it's not in the W3C spec yet
        }

        for f in files:
            dist_wrapper = ET.SubElement(root[0], "{{{dcat}}}distribution".format(**ns))
            dist = ET.SubElement(dist_wrapper, "{{{dcat}}}Distribution".format(**ns))

            for tag, func in files_fields.items():
                tag_value = func(f)

                if tag_value:
                    el = ET.SubElement(dist, tag.format(**ns))
                    if isinstance(tag_value, str):
                        el.text = tag_value
                    if isinstance(tag_value, dict):
                        el.attrib.update(tag_value)

    def transform_with_xslt(self, dc_record, **kwargs):
        """Transform record with XSLT."""
        dc_etree = schema43.dump_etree(dc_record)
        dc_namespace = schema43.ns[None]
        dc_etree.tag = "{{{0}}}resource".format(dc_namespace)
        dcat_etree = self.xslt_transform_func(dc_etree).getroot()

        # Inject files in results (since the XSLT can't do that by default)
        files_data = dc_record.get("_files", [])
        if files_data:
            self._add_files(
                root=dcat_etree,
                files=files_data,
            )
        return dcat_etree
