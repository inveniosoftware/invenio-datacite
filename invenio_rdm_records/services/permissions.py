# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
# Copyright (C) 2023 TU Wien.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Permissions for Invenio RDM Records."""

from invenio_communities.generators import CommunityCurators
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    Disable,
    IfConfig,
    SystemProcess,
)
from invenio_records_permissions.policies.records import RecordPermissionPolicy
from invenio_requests.services.permissions import (
    PermissionPolicy as RequestPermissionPolicy,
)

from ..requests.access import GuestAccessRequest
from .generators import (
    AccessGrant,
    GuestAccessRequestToken,
    IfExternalDOIRecord,
    IfFileIsLocal,
    IfNewRecord,
    IfRequestType,
    IfRestricted,
    RecordCommunitiesAction,
    RecordOwners,
    ResourceAccessToken,
    SecretLinks,
    SubmissionReviewer,
)


class RDMRecordPermissionPolicy(RecordPermissionPolicy):
    """Access control configuration for records.

    Note that even if the array is empty, the invenio_access Permission class
    always adds the ``superuser-access``, so admins will always be allowed.
    """

    NEED_LABEL_TO_ACTION = {
        "bucket-update": "update_files",
        "bucket-read": "read_files",
        "object-read": "read_files",
    }

    #
    # High-level permissions (used by low-level)
    #
    can_manage = [
        RecordOwners(),
        RecordCommunitiesAction("curate"),
        SystemProcess(),
    ]
    can_curate = can_manage + [AccessGrant("edit"), SecretLinks("edit")]
    can_review = can_curate + [SubmissionReviewer()]
    can_preview = can_curate + [
        AccessGrant("preview"),
        SecretLinks("preview"),
        SubmissionReviewer(),
    ]
    can_view = can_preview + [
        AccessGrant("view"),
        SecretLinks("view"),
        SubmissionReviewer(),
        RecordCommunitiesAction("view"),
    ]

    can_authenticated = [AuthenticatedUser(), SystemProcess()]
    can_all = [AnyUser(), SystemProcess()]

    #
    # Miscellaneous
    #
    # Allow for querying of statistics
    # - This is currently disabled because it's not needed and could potentially
    #   open up surface for denial of service attacks
    can_query_stats = [Disable()]

    #
    #  Records
    #
    # Allow searching of records
    can_search = can_all

    # Allow reading metadata of a record
    can_read = [
        IfRestricted("record", then_=can_view, else_=can_all),
    ]
    # Allow reading the files of a record
    can_read_files = [
        IfRestricted("files", then_=can_view, else_=can_all),
        ResourceAccessToken("read"),
    ]
    can_get_content_files = [
        # note: even though this is closer to business logic than permissions,
        # it was simpler and less coupling to implement this as permission check
        IfFileIsLocal(then_=can_read_files, else_=[SystemProcess()])
    ]
    # Allow submitting new record
    can_create = can_authenticated

    #
    # Drafts
    #
    # Allow ability to search drafts
    can_search_drafts = can_authenticated
    # Allow reading metadata of a draft
    can_read_draft = can_preview
    # Allow reading files of a draft
    can_draft_read_files = can_preview + [ResourceAccessToken("read")]
    # Allow updating metadata of a draft
    can_update_draft = can_review
    # Allow uploading, updating and deleting files in drafts
    can_draft_create_files = can_review
    can_draft_set_content_files = [
        # review is the same as create_files
        IfFileIsLocal(then_=can_review, else_=[SystemProcess()])
    ]
    can_draft_get_content_files = [
        # preview is same as read_files
        IfFileIsLocal(then_=can_draft_read_files, else_=[SystemProcess()])
    ]
    can_draft_commit_files = [
        # review is the same as create_files
        IfFileIsLocal(then_=can_review, else_=[SystemProcess()])
    ]
    can_draft_update_files = can_review
    can_draft_delete_files = can_review
    # Allow enabling/disabling files
    can_manage_files = [
        IfConfig(
            "RDM_ALLOW_METADATA_ONLY_RECORDS",
            then_=[IfNewRecord(then_=can_authenticated, else_=can_review)],
            else_=[],
        ),
    ]
    # Allow managing record access
    can_manage_record_access = [
        IfConfig(
            "RDM_ALLOW_RESTRICTED_RECORDS",
            then_=[IfNewRecord(then_=can_authenticated, else_=can_review)],
            else_=[],
        )
    ]

    #
    # PIDs
    #
    can_pid_create = can_review
    can_pid_register = can_review
    can_pid_update = can_review
    can_pid_discard = can_review
    can_pid_delete = can_review

    #
    # Actions
    #
    # Allow to put a record in edit mode (create a draft from record)
    can_edit = can_curate
    # Allow deleting/discarding a draft and all associated files
    can_delete_draft = can_curate
    # Allow creating a new version of an existing published record.
    can_new_version = [
        IfConfig(
            "RDM_ALLOW_EXTERNAL_DOI_VERSIONING",
            then_=can_curate,
            else_=[IfExternalDOIRecord(then_=[Disable()], else_=can_curate)],
        ),
    ]
    # Allow publishing a new record or changes to an existing record.
    can_publish = can_review
    # Allow lifting a record or draft.
    can_lift_embargo = can_manage

    #
    # Record communities
    #
    # Who can add record to a community
    can_add_community = [RecordOwners(), SystemProcess()]
    # Who can remove a community from a record
    can_remove_community = [
        RecordOwners(),
        CommunityCurators(),
        SystemProcess(),
    ]
    # Who can remove records from a community
    can_remove_record = [CommunityCurators()]

    #
    # Media files - draft
    #
    can_draft_media_create_files = can_review
    can_draft_media_read_files = can_review
    can_draft_media_set_content_files = [
        IfFileIsLocal(then_=can_review, else_=[SystemProcess()])
    ]
    can_draft_media_get_content_files = [
        # preview is same as read_files
        IfFileIsLocal(then_=can_preview, else_=[SystemProcess()])
    ]
    can_draft_media_commit_files = [
        # review is the same as create_files
        IfFileIsLocal(then_=can_review, else_=[SystemProcess()])
    ]
    can_draft_media_update_files = can_review
    can_draft_media_delete_files = can_review

    #
    # Media files - record
    #
    can_media_read_files = [
        IfRestricted("record", then_=can_view, else_=can_all),
        ResourceAccessToken("read"),
    ]
    can_media_get_content_files = [
        # note: even though this is closer to business logic than permissions,
        # it was simpler and less coupling to implement this as permission check
        IfFileIsLocal(then_=can_read, else_=[SystemProcess()])
    ]
    can_media_create__files = [Disable()]
    can_media_set_content_files = [Disable()]
    can_media_commit_files = [Disable()]
    can_media_update_files = [Disable()]
    can_media_delete_files = [Disable()]

    #
    # Disabled actions (these should not be used or changed)
    #
    # - Records/files are updated/deleted via drafts so we don't support
    #   using below actions.
    can_update = [Disable()]
    can_delete = [Disable()]
    can_create_files = [Disable()]
    can_set_content_files = [Disable()]
    can_commit_files = [Disable()]
    can_update_files = [Disable()]
    can_delete_files = [Disable()]


guest_token = IfRequestType(
    GuestAccessRequest, then_=[GuestAccessRequestToken()], else_=[]
)


class RDMRequestsPermissionPolicy(RequestPermissionPolicy):
    """Permission policy for requets, adapted to the needs for RDM-Records."""

    can_read = RequestPermissionPolicy.can_read + [guest_token]
    can_update = RequestPermissionPolicy.can_update + [guest_token]
    can_action_submit = RequestPermissionPolicy.can_action_submit + [guest_token]
    can_action_cancel = RequestPermissionPolicy.can_action_cancel + [guest_token]
