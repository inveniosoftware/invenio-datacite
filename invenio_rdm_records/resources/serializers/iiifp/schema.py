# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 data-futures.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""IIIF Presentation API Schema for Invenio RDM Records."""

from flask import current_app
from marshmallow import Schema, fields


class IIIFPresiSchema(Schema):
    """IIIF Presentation API Marshmallow Schema."""

    class Meta:  # todo: sort ordering this "should" be first.
        """Marshmallow meta class."""

        include = {
           '@context': fields.Constant(
              'http://iiif.io/api/presentation/2/context.json'
           ),
           '@type': fields.Constant("sc:Manifest"),
           '@id': fields.Method('make_manifest_id')
        }

    label = fields.String(attribute='metadata.title')
    metadata = fields.Method('make_metadata')
    description = fields.Function(
        lambda o: o["metadata"]["description"]
    )
    license = fields.Function(lambda o: o["metadata"]["rights"][0]["link"])
    attribution = fields.Function(
        lambda o: current_app.config['THEME_SITENAME']
    )
    sequences = fields.Method('make_sequence')

    def imgUriBase(self, obj):
        """Base for image API URIs."""
        return f"{current_app.config['SITE_API_URL']}/iiif/v2/{obj['id']}"

    def presiUriBase(self, obj):
        """Base for presentation API URIs."""
        return f"{current_app.config['SITE_API_URL']}/records/{obj['id']}"

    def make_manifest_id(self, obj):
        """Create maniest id."""
        return self.presiUriBase(obj) + "/iiif/manifest"

    def image_service(self, imgid, vers, level):
        """Image service generator."""
        return {
            '@id': imgid,
            '@context': f"http://iiif.io/api/image/{vers}/context.json",
            'profile': f"http://iiif.io/api/image/{vers}/level{level}.json"
        }

    def make_metadata(self, obj):
        """Generate metadata entries."""
        # to-do: more fields to show in metadata?
        m = obj["metadata"]
        if m['publication_date']:
            return [
                    {
                        'label': 'Publication Date',
                        'value': m['publication_date']
                    }
                ]

    def make_sequence(self, obj):
        """Create sequence of canvases from any image attachments. """
        canvases = []
        p = 1
        # check for width/height before including this file
        for i in obj._record.files.entries:
            try:
                w = obj._record.files.entries[i].metadata["width"]
                h = obj._record.files.entries[i].metadata["height"]
            except (AttributeError, KeyError, TypeError):
                continue

            canvases.append({
                "@id": f"{self.presiUriBase(obj)}/canvas/p{p}",
                "@type": "sc:Canvas",
                "label": f"Page {p}",
                "width": w,
                "height": h,
                "images": [
                    {
                        "@id": f"{self.presiUriBase(obj)}/canvas/p{p}/a1",
                        "@type": "oa:Annotation",
                        "on": f"{self.presiUriBase(obj)}/canvas/p{p}",
                        "motivation": "sc:painting",
                        "resource":
                            {
                                "@id": f"{self.imgUriBase(obj)}",
                                "@type": "dctypes:Image",
                                "format": "image/jpeg",
                                "width": w,
                                "height": h,
                                "service": self.image_service(
                                    imgid=f"{self.imgUriBase(obj)}:{i}",
                                    vers=2,
                                    level=2
                                )
                            }
                        }
                    ]
                }
            )
            p += 1

        return [{
            '@id': f"{self.presiUriBase(obj)}sequence/default",
            '@type': 'sc:Sequence',
            'label': 'default order',
            'viewingDirection': 'left-to-right',
            'viewingHint': 'paged',
            'canvases': canvases
        }]
