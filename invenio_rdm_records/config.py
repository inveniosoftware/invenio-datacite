# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""DataCite-based data model for Invenio."""

from invenio_indexer.api import RecordIndexer
from invenio_records_files.api import Record
from invenio_records_permissions import record_create_permission_factory, \
    record_delete_permission_factory, record_files_permission_factory, \
    record_read_permission_factory, record_search_permission_factory, \
    record_update_permission_factory
from invenio_records_permissions.api import RecordsSearch
from invenio_records_rest.facets import terms_filter


def _(x):
    """Identity function for string extraction."""
    return x


# Records Permissions

RECORDS_PERMISSIONS_RECORD_POLICY = (
    'invenio_rdm_records.permissions.RDMRecordPermissionPolicy'
)
"""PermissionPolicy used by permission factories above."""

# Files REST

FILES_REST_PERMISSION_FACTORY = record_files_permission_factory
"""Set default files permission factory."""

# Invenio-IIIF
# =================
# See https://invenio-iiif.readthedocs.io/en/latest/configuration.html

IIIF_PREVIEW_TEMPLATE = "invenio_rdm_records/iiif_preview.html"
"""Template for IIIF image preview."""

# Invenio-Previewer
# =================
# See https://github.com/inveniosoftware/invenio-previewer/blob/master/invenio_previewer/config.py  # noqa

PREVIEWER_PREFERENCE = [
    'csv_dthreejs',
    'iiif_image',
    'simple_image',
    'json_prismjs',
    'xml_prismjs',
    'mistune',
    'pdfjs',
    'ipynb',
    'zip',
]
"""Preferred previewers."""

# Invenio-Records-UI
# ==================
# See https://invenio-records-ui.readthedocs.io/en/latest/configuration.html

RECORDS_UI_ENDPOINTS = {
    'recid': {
        'pid_type': 'recid',
        'record_class': 'invenio_records_files.api:Record',
        'route': '/records/<pid_value>',
        'template': 'invenio_rdm_records/record_landing_page.html'
    },
    'recid_files': {
        'pid_type': 'recid',
        'record_class': 'invenio_records_files.api:Record',
        'route': '/records/<pid_value>/files/<path:filename>',
        'view_imp': 'invenio_records_files.utils.file_download_ui',
    },
    'recid_previewer': {
        'pid_type': 'recid',
        'record_class': 'invenio_records_files.api:Record',
        'route': '/records/<pid_value>/preview/<path:filename>',
        'view_imp': 'invenio_previewer.views.preview',
    },
}

#: Allow list of contributor types.
RECORD_CONTRIBUTOR_TYPES = [
    dict(label='Contact person', datacite='ContactPerson'),
    dict(label='Data collector', datacite='DataCollector'),
    dict(label='Data curator', datacite='DataCurator'),
    dict(label='Data manager', datacite='DataManager'),
    dict(label='Distributor', datacite='Distributor'),
    dict(label='Editor', datacite='Editor'),
    dict(label='Hosting institution', datacite='HostingInstitution'),
    dict(label='Other', datacite='Other'),
    dict(label='Producer', datacite='Producer'),
    dict(label='Project leader', datacite='ProjectLeader'),
    dict(label='Project manager', datacite='ProjectManager'),
    dict(label='Project member', datacite='ProjectMember'),
    dict(label='Registration agency', datacite='RegistrationAgency'),
    dict(label='Registration authority', datacite='RegistrationAuthority'),
    dict(label='Related person', datacite='RelatedPerson'),
    dict(label='Researcher', datacite='Researcher'),
    dict(label='Research group', datacite='ResearchGroup'),
    dict(label='Rights holder', datacite='RightsHolder'),
    dict(label='Sponsor', datacite='Sponsor'),
    dict(label='Supervisor', datacite='Supervisor'),
    dict(label='Work package leader', datacite='WorkPackageLeader'),
    dict(label='Other', datacite='Other')
]

RECORD_CONTRIBUTOR_TYPES_LABELS = {
    x['datacite']: x['label'] for x in RECORD_CONTRIBUTOR_TYPES
}

"""Records UI for RDM Records."""

# Records Files

RECORDS_FILES_REST_ENDPOINTS = {
    'RECORDS_REST_ENDPOINTS': {
        'recid': '/files',
    }
}
"""Set default files rest endpoints."""

PIDSTORE_RECID_FIELD = 'recid'

# Invenio-Formatter
# =================

FORMATTER_BADGES_ALLOWED_TITLES = ['DOI', 'doi']
"""List of allowed titles in badges."""

FORMATTER_BADGES_TITLE_MAPPING = {'doi': 'DOI'}
"""Mapping of titles."""

# Invenio-RDM-Records
# ===================

RDM_RECORDS_LOCAL_DOI_PREFIXES = ['10.9999']
"""List  of locally managed DOI prefixes."""

RDM_RECORDS_METADATA_NAMESPACES = {}
"""Namespaces for fields *added* to the metadata schema.

Of the shape:

.. code-block:: python

    {
        '<prefix1>': {
            '@context': '<url>'
        },
        # ...
        '<prefixN>': {
            '@context': '<url>'
        }
    }

For example:

.. code-block:: python

    {
        'dwc': {
            '@context': 'http://rs.tdwg.org/dwc/terms/'
        },
        'z':{
            '@context': 'https://zenodo.org/terms'
        }
    }

Use :const:`invenio_rdm_records.config.RDM_RECORDS_METADATA_EXTENSIONS` to
define the added fields.

See :class:`invenio_rdm_records.metadata_extensions.MetadataExtensions` for
how this configuration variable is used.
"""

RDM_RECORDS_METADATA_EXTENSIONS = {}
"""Fields added to the metadata schema.

Of the shape:

.. code-block:: python

    {
        '<prefix1>:<field1>': {
            'elasticsearch': '<allowed elasticsearch type>'
            'marshmallow': '<allowed marshmallow type>'
        },
        # ...
        '<prefixN>:<fieldN>': {
            'elasticsearch': '<allowed elasticsearch type>'
            'marshmallow': '<allowed marshmallow type>'
        }
    }

For example:

.. code-block:: python

    {
        'dwc:family': {
            'elasticsearch': 'keyword',
            'marshmallow': SanitizedUnicode()
        },
        'dwc:behavior': {
            'elasticsearch': 'text',
            'marshmallow': SanitizedUnicode()
        },
        'z:department': {
            'elasticsearch': 'text',
            'marshmallow': SanitizedUnicode()
        }
    }

Use :const:`invenio_rdm_records.config.RDM_RECORDS_METADATA_NAMESPACES` to
define the prefixes.

See :class:`invenio_rdm_records.metadata_extensions.MetadataExtensions` for
allowed types and how this configuration variable is used.
"""

RDM_RECORDS_CUSTOM_VOCABULARIES = {}
"""Paths to custom controlled vocabularies.

Of the shape:

.. code-block:: python

    {
        '<dotted>.<path>.<to field1>': {
            'path': '<absolute path to CSV file containing it>'
        },
        # ...
        '<dotted>.<path>.<to fieldN>': {
            'path': '<absolute path to CSV file containing it>'
        }
    }

For example:

.. code-block:: python

    {
        'resource_type': {
            'path': os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'my_resource_types.csv'
            )
        },
        'contributors.role': {
            'path': os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'my_contributor_roles.csv'
            )
        }
    }
"""

RDM_RECORDS_UI_EDIT_URL = "/uploads/<pid_value>"
"""Default UI URL for the edit page of a Bibliographic Record."""

#: Default site URL (used only when not in a context - e.g. like celery tasks).
THEME_SITEURL = "http://localhost:5000"
