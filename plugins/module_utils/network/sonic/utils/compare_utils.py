#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# compare_utils
import os
import yaml
import json
from copy import deepcopy

from ansible.module_utils._text import to_text
from ansible.utils.display import Display
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    remove_empties,
    validate_config,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils import (
    Constant,
    log,
    log_vars
)

# Method to check listPath syntax (listName[<key1>|<more keys>]) or not
def isListPathSyntax(name):
    result = False

    if Constant.LIST_KEY_OPEN_CHAR in name and \
       Constant.LIST_KEY_CLOSE_CHAR in name:
        result = True

    return result

# Method to parse listPath syntax (listName[<key1>|<more keys>]
def parseListPath(path):
    listName = None
    keys = None

    if path:
        tmpParts = path.split(Constant.LIST_KEY_OPEN_CHAR)
        listName = tmpParts[0]
        if len(tmpParts) > 1:
            pathLeft = tmpParts[1]
            keys = pathLeft.split(Constant.LIST_KEY_CLOSE_CHAR)[0]

    return listName, keys

# Expand facts method
def expandFacts(facts, listPaths):
    """
    @brief Expand facts - list of dicts as dict of dicts
           required to find diff between two dicts

    @param facts (dict): Facts data
    @param listPaths(list): List of paths to be expanded

    @returns expandedFacts (dict)
    """
    # Internal method to expand list of dict as dict of dicts
    def expandFactsInternal(pathIt, nodes):
        listName = None
        keys = None
        nodeName = None

        # 1. Extract token
        token = next(pathIt, None)
        if not token:
            # log("Token is empty")
            return

        # 2. Extract tokenVal
        tokenVal = token[1]
        # 3. If list path syntax is available, extract listName & keys
        if isListPathSyntax(tokenVal):
            # Parse listPath syntax
            listName, keys = parseListPath(tokenVal)
            # log_vars(listName=listName, keys=keys)
        # 4. Proceed to next token, if not list path syntax
        else:
            nodeName = tokenVal
            if nodeName in nodes:
                expandFactsInternal(pathIt, nodes[nodeName])
            else:
                # log(f"Node {nodeName} not present")
                pass
            return

        # 5. Return when unable to fetch listName or keys
        if not listName or not keys:
            log(f"Failed to get listName & keys from {tokenVal}")
            return

        # 6. Return when nodes do not have listName key
        if not listName in nodes:
            log(f"List items of {listName} are empty")
            return

        listNode = nodes.get(listName, None)
        # 7. List is not expanded yet
        if isinstance(listNode, list):
            # log("Expanding list of dicts")
            # 7.1. Take out listNode items
            listNode = nodes.pop(listName, None)
            # 7.2. Parse key names
            listKeys = keys.split(Constant.DELIMITER_LIST_KEYS)
            # 7.3. Expand list items
            dicts = dict()
            for listEntry in listNode:
                dictNode = dict()
                keyVals = list()
                for listKey in listKeys:
                    valTmp = listEntry.get(listKey, None)
                    # Skip adding the key, if not present
                    # This is valid for optional keys
                    if not valTmp: continue
                    keyVal = listKey + Constant.DELIMITER_LIST_KEY_PAIR + \
                             str(valTmp)
                    keyVals.append(keyVal)
                dictKey = Constant.DELIMITER_LIST_KEYS.join(keyVals)
                # 7.3.1. Create temp node with key node values combined as key
                # log_vars(dictKey=dictKey)
                dicts.update({dictKey: listEntry})
            # 7.4. Update expanded dicts in respective facts node
            nodes.update({listName: dicts})

        # 8. List is expanded already
        # Call expandFactsInternal for each item in expanded items
        listNode = nodes.get(listName, None)
        if isinstance(listNode, dict):
            # log("Processing dicts")
            listNode = nodes.get(listName, None)
            for key, listEntry in listNode.items():
                # log_vars(key=key, pathIt=pathIt)
                pathItCopy = deepcopy(pathIt)
                expandFactsInternal(pathItCopy, listEntry)
        else:
            log("Instance of {listName} is neither list nor dict")
            return

        return

    # Main method starts here
    # 1. Start from facts
    factsNode = facts
    if not factsNode:
        log(f"factsNode is empty")
        return

    # 2. Iterate all nodes in listPaths, for each list item
    for listPath in listPaths:
        # log_vars(listPath=listPath)
    #    2.1 get list path, key of listPaths dict is list path
        listPathParts = listPath.split(Constant.DELIMITER_LIST_PATH)
        listPathIt = enumerate(listPathParts)
    #    2.2 call expandFactsInternal for listPath item
        expandFactsInternal(listPathIt, factsNode)

    return


# Compress facts
def compressFacts(facts, listPaths):
    """
    @brief Compress facts - dict of dicts as list of dicts

    @param facts (dict): Facts data
    @param listPaths(list): List of paths to be expanded

    @returns compressedFacts (dict)
    """
    # Internal method to compress dict of dicts as list of dicts
    def compressFactsInternal(pathIt, nodes):
        # 1. Extract token
        token = next(pathIt, None)
        if not token:
            # log("Token is empty")
            return

        # 2. Extract tokenVal
        tokenVal = token[1]
        # 3. If list path syntax is available, extract listName & keys
        if isListPathSyntax(tokenVal):
            # Parse listPath syntax
            listName, keys = parseListPath(tokenVal)
            # log_vars(listName=listName, keys=keys)
        # 4. Proceed to next token, if not list path syntax
        else:
            nodeName = tokenVal
            if nodeName in nodes:
                compressFactsInternal(pathIt, nodes[nodeName])
            else:
                # log(f"Node {nodeName} not present")
                pass
            return

        # 5. Return when unable to fetch listName or keys
        if not listName or not keys:
            log(f"Failed to get listName & keys from {tokenVal}")
            return

        # 6. Return when nodes do not have listName key
        if not listName in nodes:
            log(f"List items of {listName} are empty")
            return

        listNode = nodes.get(listName, None)
        # 7. List is not compressed yet
        if isinstance(nodes[listName], dict):
            # log("Compressing dict of dicts")
            # 7.1. Take out listNode items
            listNode = nodes.pop(listName, None)
            # 7.2. compress list items
            listItems = list()
            # 7.3. iterate each item in dict
            for key, node in listNode.items():
                # log_vars(key=key)
            # 7.3.1 append value alone into temp list
                listItems.append(node)
            # 7.4. Update compressed dicts in respective facts node
            nodes.update({listName: listItems})

        # 8. List is compressed already
        # Call compressFactsInternal for each item in compressed items
        listNode = nodes.get(listName, None)
        if isinstance(nodes[listName], list):
            # log("Processing list")
            listNode = nodes.get(listName, None)
            for listEntry in listNode:
                # log_vars(pathIt=pathIt)
                pathItCopy = deepcopy(pathIt)
                compressFactsInternal(pathItCopy, listEntry)
        else:
            log("Instance of {listName} is neither list nor dict")
            return

        return

    # Main method starts here
    # 1. Start from facts
    factsNode = facts
    if not factsNode:
        log(f"factsNode is empty")
        return

    # 2. Iterate all nodes in listPaths, for each list item
    for listPath in listPaths:
        # log_vars(listPath=listPath)
    #    2.1 get list path, key of listPaths dict is list path
        listPathParts = listPath.split(Constant.DELIMITER_LIST_PATH)
        listPathIt = enumerate(listPathParts)
    #    2.2 call compressFactsInternal for listPath item
        compressFactsInternal(listPathIt, factsNode)

    return

# Class to compare two dicts and populate matching, not-matching items
# in separate fields (baseOnly, match, diff, comparableOnly)
class CompareDict(object):

    def __init__(self, base, comparable):
        # Members
        self._base = base
        self._comparable = comparable

        self._baseOnly = dict()
        self._match = dict()
        self._diff = dict()
        self._comparableOnly = dict()

    @property
    def base(self):
        return self._base

    @property
    def comparable(self):
        return self._comparable

    @property
    def baseOnly(self):
        return self._baseOnly

    @baseOnly.setter
    def baseOnly(self, value):
        self._baseOnly = value

    @property
    def match(self):
        return self._match

    @match.setter
    def match(self, value):
        self._match = value

    @property
    def diff(self):
        return self._diff

    @diff.setter
    def diff(self, value):
        self._diff = value

    @property
    def comparableOnly(self):
        return self._comparableOnly

    @comparableOnly.setter
    def comparableOnly(self, value):
        self._comparableOnly = value

    def dump(self):
        prettyJson = json.dumps(self.base, indent=4)
        log(f"base")
        log(f"{prettyJson}")
        prettyJson = json.dumps(self.comparable, indent=4)
        log(f"comparable")
        log(f"{prettyJson}")
        prettyJson = json.dumps(self.baseOnly, indent=4)
        log(f"baseOnly")
        log(f"{prettyJson}")
        prettyJson = json.dumps(self.match, indent=4)
        log(f"match")
        log(f"{prettyJson}")
        prettyJson = json.dumps(self.diff, indent=4)
        log(f"diff")
        log(f"{prettyJson}")
        prettyJson = json.dumps(self.comparableOnly, indent=4)
        log(f"comparableOnly")
        log(f"{prettyJson}")

    def compare(self):
        # Internal method to compare two dicts
        def compareInternal(base, comparable):
            baseOnly = dict()
            match = dict()
            diff = dict()

            # log_vars(base=base, comparable=comparable)
            # 1. Iterate each item in base
            for baseKey, baseItem in base.items():
                # log(f"Processing {baseKey}")
            # 2. If item is not present in comparable,
                if not baseKey in comparable:
                    # log(f"{baseKey} is not present in comparable")
            #    - add item in baseOnly
                    baseOnly.update({baseKey: baseItem})
            # 3. If item is present in comparable
                else:
                    comparableItem = comparable.get(baseKey, None)
            #    - If item value is dict
                    if isinstance(baseItem, dict):
                        # log(f"{baseKey} is dict")
            #      - Call recursively with item value of base & comparable
                        baseOnlyTmp, matchTmp, diffTmp = \
                                compareInternal(baseItem, comparableItem)
                        # log_vars(baseOnlyTmp=baseOnlyTmp, matchTmp=matchTmp, diffTmp=diffTmp)
            #      - Append above return values to current nodes result
                        if baseOnlyTmp:
                            baseOnly.update({baseKey: baseOnlyTmp})
                        if matchTmp:
                            match.update({baseKey: matchTmp})
                        if diffTmp:
                            diff.update({baseKey: diffTmp})
            #    - If item value is not dict
                    else:
            #      - If values of base and comparable are same
                        if baseItem == comparableItem:
                            # log(f"{baseKey} is matching with comparable")
            #        - add item to match
                            match.update({baseKey: baseItem})
            #      - If values of base and comparable are different
                        else:
            #        - create two nodes with comparable & base value
                            # log(f"{baseKey} is not matching with comparable")
                            diffNode = dict()
                            diffNode.update({Constant.BASE_VAL_STR: baseItem})
                            diffNode.update({Constant.COMPARABLE_VAL_STR: comparableItem})
            #        - add item to diff
                            diff.update({baseKey: diffNode})
            # 4. Return
            return baseOnly, match, diff

        # Internal method to find new nodes in base only
        def findNewNodes(base, comparable):
            baseOnly = dict()
            # 1. Iterate each item in base
            for baseKey, baseItem in base.items():
            # 2. If item is not present in comparable,
                if not baseKey in comparable:
            #    - add item in baseOnly
                    baseOnly.update({baseKey: baseItem})
            # 3. If item is present in comparable
                else:
                    comparableItem = comparable.get(baseKey, None)
            #    - If item value is dict
                    if isinstance(baseItem, dict):
            #      - Call recursively with item value of base & comparable
                        baseOnlyTmp = findNewNodes(baseItem, comparableItem)
            #      - Append above return values to current nodes result
                        if baseOnlyTmp:
                            baseOnly.update({baseKey: baseOnlyTmp})
            # 4. Return
            return baseOnly

        # Add missing mandator keys (as per argspec)
        # baseOnly will miss the key nodes when matched with comparable items
        def addMandatoryKeys(data):
            if not data or not isinstance(data, dict):
                return

            for key, item in data.items():
                # log(f"Processing {key}, {item}")
                if Constant.DELIMITER_LIST_KEY_PAIR in key:
                    keys = key.split(Constant.DELIMITER_LIST_KEYS)
                    # log_vars(keys=keys)
                    for keyTmp in keys:
                        keyParts = keyTmp.split(Constant.DELIMITER_LIST_KEY_PAIR)
                        keyName = keyParts[0]
                        keyVal = keyParts[1]
                        # log_vars(keyName=keyName, keyVal=keyVal)
                        if keyName not in item:
                            log(f"Added mandatory pair {keyName}={keyVal}")
                            item.update({keyName: keyVal})
                # Call recursively to handle inner dicts
                if isinstance(item, dict):
                    addMandatoryKeys(item)

            return

        # Main method starts from here

        # 1. If base is empty or not a dict, return comparable
        #    as comparableOnly
        if not self.base or not isinstance(self.base, dict):
            self.comparableOnly = self.comparable
            return

        # 2. If comparable is empty or not a dict, return base
        #    as baseOnly
        if not self.comparable or not isinstance(self.comparable, dict):
            self.baseOnly = self.base
            return

        # 3. Call compareInternal with base, comparable sequence and
        #    save return values in baseOnly, match & diff
        self.baseOnly, self.match, self.diff, = compareInternal(self.base,
                                                                self.comparable)
        # 4. Call findNewNodes with comparable, base sequence and
        #    save return value as comparableOnly
        self.comparableOnly = findNewNodes(self.comparable, self.base)

        # 5. Add mandatory keys in baseOnly nodes
        log("Adding mandatory keys for baseOnly")
        addMandatoryKeys(self.baseOnly)
        log("Adding mandatory keys for diff")
        addMandatoryKeys(self.diff)
        log("Adding mandatory keys for match")
        addMandatoryKeys(self.match)
        log("Adding mandatory keys for comparableOnly")
        addMandatoryKeys(self.comparableOnly)

        # 6. Return
        return

    def compareNew(self):
        def compareInternal(want, have):
            wOnly = dict()
            match = dict()
            diff = dict()
            hOnly = dict()

            # Boundary cases
            # 1. want is empty - save have in haveOnly & return
            if not want:
                hOnly = have
                return
            # 2. have is empty - save want in wantOnly & return
            if not have:
                wOnly = want
                return
            # Iterate all items in want
            for wKey, wItem in want.items():
                hItem = have.get(wKey, None)
            #   If want item is not present in have, add item into wantOnly
                if not hItem:
                    wOnly.update({wKey: wItem})
            #   If want item is present in have,
                else:
            #       If item is dict
                    if isinstance(wItem, dict) and isinstance(hItem, dict):
            #           call compareNew recursively
                        wOnlyTmp, matchTmp, diffTmp, hOnlyTmp = compareInternal(wItem, hItem)
            #           add return values (wantOnly, match, diff, haveOnly) into item
                        if wOnlyTmp:
                            wOnly.update({wKey: wOnlyTmp})
                        if matchTmp:
                            match.update({wKey: matchTmp})
                        if diffTmp:
                            diff.update({wKey: diffTmp})
                        if hOnlyTmp:
                            hOnly.update({wKey: hOnlyTmp})
            #       If item is not dict
                    else:
            #           compare want item value against have item value
            #           if both values match, add item into match dict
                        if wItem == hItem:
                            match.update({wKey: wItem})
            #           if both values differ, add item into diff dict with want & have values
                        else:
                            diffNode = dict()
                            diffNode.update({WANT_VALUE_KEY: wItem})
                            diffNode.update({HAVE_VALUE_KEY: hItem})
                            diff.update({wKey: diffNode})
            #           return match & diff dicts
            # Iterate all items in have
            for hKey, hItem in have.items():
            #   If have item is not present in want, add item into haveOnly
                if hKey not in want:
                    hOnly.update({hKey: hItem})
            #
            # return baseOnly, match, diff, haveOnly
            return wOnly, match, diff, hOnly

        # Main method

        WANT_ONLY_NODES_KEY = 'want-only'
        MATCH_NODES_KEY = 'match'
        DIFF_NODES_KEY = 'diff'
        HAVE_ONLY_NODES_KEY = 'have-only'
        WANT_VALUE_KEY = 'want-value'
        HAVE_VALUE_KEY = 'have-value'
        result = dict()
        # Boundary cases
        # 1. want is empty - save have in haveOnly & return
        if not self.base:
            hOnly = self.comparable
            result.update({HAVE_ONLY_NODES_KEY: hOnly})
            return result
        # 2. have is empty - save want in wantOnly & return
        if not self.comparable:
            wOnly = self.base
            result.update({WANT_ONLY_NODES_KEY: wOnly})
            return result

        wOnly, match, diff, hOnly = compareInternal(self.base, self.comparable)
        # Update result
        if wOnly:
            result.update({WANT_ONLY_NODES_KEY: wOnly})
        if match:
            result.update({MATCH_NODES_KEY: match})
        if diff:
            result.update({DIFF_NODES_KEY: diff})
        if hOnly:
            result.update({HAVE_ONLY_NODES_KEY: hOnly})

        return result
