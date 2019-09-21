#!/usr/bin/env python3
#
# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology-wikidata-bot
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import requests


_USER_AGENT = 'repology-wiki-bot/0.0.1'


@dataclass
class _RepologyProjectPackages:
    name: str
    packages: List[Dict[str, Any]]


@dataclass
class RepologyProject:
    name: str
    package_names_by_repo: Dict[str, List[str]]


def _iterate_repology_project_packages(apiurl: str, begin_name: Optional[str] = None, end_name: Optional[str] = None, inrepo: str = 'wikidata') -> Iterable[_RepologyProjectPackages]:
    """Iterate all repology projects present in a given repository."""
    headers = {'User-agent': _USER_AGENT}

    pivot = begin_name

    while True:
        if pivot is None:
            # fetching first page
            data = requests.get('{}?inrepo={}'.format(apiurl, inrepo), headers=headers, timeout=60).json()
            if len(data) == 0:
                break
        else:
            # fetching subsequent page
            data = requests.get('{}{}/?inrepo={}'.format(apiurl, pivot, inrepo), headers=headers, timeout=60).json()
            if len(data) <= 1:
                break

        # iterate all packages got from Repology and group by repository
        for name, packages in data.items():
            if name == pivot:
                continue
            if name >= end_name:
                return

            yield _RepologyProjectPackages(name, packages)

        pivot = max(data.keys())


def iterate_repology_projects(apiurl: str, begin_name: Optional[str] = None, end_name: Optional[str] = None) -> Iterable[RepologyProject]:
    for project in _iterate_repology_project_packages(apiurl, begin_name, end_name):
        package_names_by_repo: Dict[str, List[str]] = defaultdict(list)

        for package in project.packages:
            if 'keyname' in package:
                package_names_by_repo[package['repo']].append(package['keyname'])

        package_names_by_repo = {repo: sorted(set(project_names)) for repo, project_names in package_names_by_repo.items()}

        yield RepologyProject(project.name, package_names_by_repo)