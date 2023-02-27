# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""RDM service component for access integration."""

from invenio_access.permissions import system_process
from invenio_drafts_resources.services.records.components import ServiceComponent
from invenio_i18n import gettext as _
from marshmallow import ValidationError


class AccessComponent(ServiceComponent):
    """Service component for access integration."""

    def _populate_access_and_validate(self, identity, data, record, **kwargs):
        """Populate and validate the record's access field."""
        errors = []
        if record is not None and "access" in data:
            access = data.get("access", {})

            # Explicit permission check for modifying record access. This is inflexible,
            # but generalizing management permissions per-field is difficult.
            new_record_access = access.get("record")
            if record.access.protection.record != new_record_access:
                can_manage = self.service.check_permission(
                    identity, "manage_record_access"
                )
                if not can_manage:
                    # Set the data to what it was before
                    if "record" in access:
                        access["record"] = record.access.protection.record
                    errors.append(
                        _("You don't have permissions to manage record access.")
                    )

            # populate the record's access field with the data already
            # validated by marshmallow
            record.update({"access": access})
            record.access.refresh_from_dict(record.get("access"))

        errors.extend(record.access.errors)
        if errors:
            # filter out duplicate error messages
            messages = list({str(e) for e in errors})
            raise ValidationError(messages, field_name="access")

    def _init_owners(self, identity, record, **kwargs):
        """If the record has no owners yet, add the current user."""
        # if the given identity is that of a user, we add the
        # corresponding user to the owners
        # (record.parent.access.owners) and commit the parent
        # otherwise, the parent's owners stays empty
        is_sys_id = system_process in identity.provides
        if not record.parent.access.owners and not is_sys_id:
            owner_dict = {"user": identity.id}
            record.parent.access.owners.add(owner_dict)

    def create(self, identity, data=None, record=None, **kwargs):
        """Add basic ownership fields to the record."""
        self._populate_access_and_validate(identity, data, record, **kwargs)
        self._init_owners(identity, record, **kwargs)

    def update_draft(self, identity, data=None, record=None, **kwargs):
        """Update handler."""
        self._populate_access_and_validate(identity, data, record, **kwargs)

    def publish(self, identity, draft=None, record=None, **kwargs):
        """Update draft metadata."""
        record.access = draft.access

    def edit(self, identity, draft=None, record=None, **kwargs):
        """Update draft metadata."""
        draft.access = record.access

    def new_version(self, identity, draft=None, record=None, **kwargs):
        """Update draft metadata."""
        draft.access = record.access
