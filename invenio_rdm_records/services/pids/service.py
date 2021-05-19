# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""RDM Record Pids Service."""

from flask_babelex import lazy_gettext as _
from invenio_db import db
from invenio_drafts_resources.services.records import RecordService
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from marshmallow.exceptions import ValidationError


class PIDSService(RecordService):
    """RDM record pids service."""

    def get_client(self, client_name):
        """Get the provider client from config."""
        client_class = self.config.pids_providers_clients[client_name]
        return client_class(name=client_name)

    def get_managed_provider(self, providers_dict):
        """Get the provider set as system managed."""
        for name, attrs in providers_dict.items():
            if attrs["system_managed"]:
                return name, attrs

    def get_required_provider(self, providers_dict):
        """Get the provider set as required."""
        for name, attrs in providers_dict.items():
            if attrs["required"]:
                return name, attrs

    def get_provider(self, scheme, provider_name=None, client_name=None):
        """Get a provider from config."""
        try:
            providers = self.config.pids_providers[scheme]

            if provider_name:
                provider_config = providers[provider_name]
            else:
                # if no name provided, one of the configured must be required
                _provider = self.get_required_provider(providers)
                if not _provider:
                    # there are no required providers
                    return None
                else:
                    name, provider_config = _provider

            provider_class = provider_config["provider"]
        except ValueError:
            raise ValidationError(
                message=_(f"Unknown PID provider for {scheme}"),
                field_name=f"pids.{scheme}",
            )

        try:
            if client_name:
                client = self.get_client(client_name)
                return provider_class(client)
            elif provider_config["system_managed"]:
                # use as default the client configured for the provider
                provider_name = provider_class.name
                client = self.get_client(provider_name)
                return provider_class(client)

            return provider_class()
        except ValueError:
            raise ValidationError(
                message=_(f"{client_name} not supported for PID {scheme}"),
                ield_name=f"pids.{scheme}",
            )

    def reserve(self, id_, identity, pid_type, pid_client=None):
        """Reserve PID for a given record."""
        draft = self.draft_cls.pid.resolve(id_, registered_only=False)

        # Permissions
        self.require_permission(identity, "pid_reserve", record=draft)

        providers = self.config.pids_providers[pid_type]
        _provider = self.get_managed_provider(providers)
        if not _provider:
            raise Exception(f"No managed provider configured for {pid_type}.")

        provider_name, _ = _provider
        provider = self.get_provider(pid_type, provider_name=provider_name,
                                     client_name=pid_client)
        pid = provider.create(draft)

        draft.pids[pid_type] = {
            "identifier": pid.pid_value,
            "provider": provider.name
        }
        if provider.client:
            draft.pids[pid_type]["client"] = provider.client.name

        provider.reserve(pid, draft)
        draft.commit()

        db.session.commit()
        self.indexer.index(draft)

        return self.result_item(
            self,
            identity,
            draft,
            links_tpl=self.links_item_tpl,
        )

    def resolve(self, id_, identity, pid_type):
        """Resolve PID to a record."""
        pid = PersistentIdentifier.get(pid_type=pid_type, pid_value=id_)

        # get related record/draft
        record = self.record_cls.get_record(pid.object_uuid)

        # permissions
        self.require_permission(identity, "read", record=record)

        return self.result_item(
            self,
            identity,
            record,
            links_tpl=self.links_item_tpl,
        )

    def discard(self, id_, identity, pid_type, pid_client=None):
        """Discard a previously reserved PID for a given record.

        It will be soft deleted if already registered.
        """
        draft = self.draft_cls.pid.resolve(id_, registered_only=False)

        # Permissions
        self.require_permission(identity, "pid_delete", record=draft)

        providers = self.config.pids_providers[pid_type]
        _provider = self.get_managed_provider(providers)
        if not _provider:
            raise Exception(f"No managed provider configured for {pid_type}.")

        provider_name, _ = _provider
        provider = self.get_provider(pid_type, provider_name=provider_name,
                                     client_name=pid_client)
        pid_attr = draft.pids[pid_type]

        try:
            pid = provider.get_by_record(
                draft.id,
                pid_type=pid_type,
                pid_value=pid_attr["identifier"],
            )
        except PIDDoesNotExistError:
            raise ValidationError(
                message=_(f"No registered PID found for type {pid_type}"),
                field_name=f"pids.{pid_type}",
            )

        provider.delete(pid, draft)
        draft.pids.pop(pid_type)
        draft.commit()

        db.session.commit()
        self.indexer.index(draft)

        return self.result_item(
            self,
            identity,
            draft,
            links_tpl=self.links_item_tpl,
        )
