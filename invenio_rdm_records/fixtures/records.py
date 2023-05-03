# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Communities fixture module."""

from ..utils import get_or_create_user
from .fixture import FixtureMixin


class RecordsFixture(FixtureMixin):
    """Records fixture."""

    def __init__(self, search_paths, filename, create_record_func, delay=True):
        """Initialize the record's fixture."""
        super().__init__(search_paths, filename, create_record_func, delay)
        self.admin = None

    def create(self, entry):
        """Load a single record."""
        if self.admin is None:
            self.admin = get_or_create_user("admin@inveniosoftware.org")
        self.create_record(self.admin.id, entry, publish=True)
