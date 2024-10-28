#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# sonic_cli
import json
import re
from copy import deepcopy
from collections import OrderedDict

from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.sonic_network_config import (
    SonicNetworkConfig,
)
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import (
    ConfigLine,
)
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    remove_empties,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.sonic import (
    run_commands,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.conv_utils import (
    translate,
    Constant as ConvUtilsConstant,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.validate_utils import (
    validate,
    ValueCheckConstant
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.compare_utils import (
    isListPathSyntax,
    CompareDict,
    expandFacts,
    compressFacts,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils import (
    Constant,
    log,
    log_vars
)

from ansible.utils.display import Display
display = Display()

# Common methods

def strToBool(inVal):
    result = None
    if inVal.lower() == 'true':
        result = True
    elif inVal.lower() == 'false':
        result = False
    else: pass

    log_vars(inVal=inVal, result=result)
    return result

# This method is intended to negate a command, ie,
# add 'no' if not present
# remove 'no' if present
def negateCommand(commandParts):
    # Return when commandParts is empty
    if not commandParts:
        return

    cmd = Constant.CLI_COMMAND_NO_KEYWORD_TOKEN
    # Return when "no" prefix is present already
    if commandParts[0] == cmd:
        commandParts.remove(cmd)
    else:
        commandParts.insert(0, cmd)

    log_vars(commandParts=commandParts)
    return

# Split line by number of required parts
def splitLine(line, delimiter, numberOfParts):
    secondPart = None
    # 1. Split the line with DELIMITER_CLI_COMMAND_WORD by one occurance
    lineParts = line.split(delimiter, numberOfParts)
    count = 0
    firstPart = ''
    while count < numberOfParts:
        firstPart = firstPart + lineParts[count]
        count = count + 1

    if len(lineParts) > numberOfParts:
        secondPart = lineParts[numberOfParts]

    return firstPart, secondPart

# Check whether a name indicates ParamNode or not
def isParamNode(name):
    if name and name.startswith(Constant.PARAMETER_INDICATOR):
        return True
    else:
        return False

# Check whether a name has IF_PARENT_VAL_INDICATOR
def hasOptional(name):
    result = False
    firstPart, secondPart = splitLine(name, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
    log_vars(firstPart=firstPart, secondPart=secondPart)
    if firstPart:
        if Constant.OPTIONAL_INDICATOR in firstPart:
            result = True

    return result

# Check whether a name has IF_PARENT_VAL_INDICATOR
def hasIfParentVal(name):
    firstPart, secondPart = splitLine(name, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
    if firstPart and Constant.IF_PARENT_VAL_INDICATOR in firstPart:
        log_vars(firstPart=firstPart)
        return True
    else:
        return False

# Get param name from token
def getParamName(name):
    result = None
    nameParts = name.split(Constant.PARAMETER_INDICATOR)

    if len(nameParts) > 1:
        result = nameParts[1]

    return result

# Method to build listPath syntax (listName[<key1>|<more keys>]
def buildListPath(name, keys):
    result = ''

    if not name or not keys:
        return result
    result = name + Constant.LIST_KEY_OPEN_CHAR + keys + Constant.LIST_KEY_CLOSE_CHAR

    return result

# Method to convert parts (list) to command
def convertToCommand(parts):
    result = None

    if parts:
        parts = list(map(str, parts))
        result = Constant.DELIMITER_CLI_COMMAND_WORD.join(parts)

    return result

# Method to add commands to config
def addToConfig(config, commands, parentCommands):

    # Return for empty input value
    if not commands:
        return

    # Convert commands into list, if not already
    if isinstance(commands, str):
        commandsLocal = list()
        commandsLocal.append(commands)
    else:
        commandsLocal = commands

    # Convert parentCommands into list, if not already
    if isinstance(parentCommands, str):
        parentCommandsLocal = list()
        parentCommandsLocal.append(parentCommands)
    else:
        parentCommandsLocal = parentCommands

    log_vars(commandsLocal=commandsLocal, parentCommandsLocal=parentCommandsLocal)
    config.add(commandsLocal, parents=parentCommandsLocal)

class AnsibleWord(object):

    """
    AnsibleWord Class
    """
    # Methods
    def __init__(self, word=None):
        # Members
        self._ansibleName = None
        self._listName = None
        self._listKeys = None
        self._interfaceList = False
        self._listGroup = False
        self._interfaceParam = False
        self._ansibleValue = None
        self._skip = None
        self._optional = None
        self._ignoreValForDelete = False
        self._negateCommand = None
        self._mergeAsReplace = False
        self._translateMethod = None
        self._valueCheckMethod = None
        self._ifFactsPresent = None
        self._ifNextValue = None
        self._parentName = None
        self._exitCmd = None
        self._ifParentValue = None
        self._noParam = False

        self.parse(word)

    @property
    def ansibleName(self):
        return self._ansibleName

    @ansibleName.setter
    def ansibleName(self, value):
        self._ansibleName = value

    @property
    def listName(self):
        return self._listName

    @listName.setter
    def listName(self, value):
        self._listName = value

    @property
    def listKeys(self):
        return self._listKeys

    @listKeys.setter
    def listKeys(self, value):
        self._listKeys = value

    def listKeysAppend(self, value):
        if not self._listKeys:
            self._listKeys = list()
        self._listKeys.append(value)

    @property
    def interfaceList(self):
        return self._interfaceList

    @interfaceList.setter
    def interfaceList(self, value):
        self._interfaceList = value

    @property
    def listGroup(self):
        return self._listGroup

    @listGroup.setter
    def listGroup(self, value):
        self._listGroup = value

    @property
    def interfaceParam(self):
        return self._interfaceParam

    @interfaceParam.setter
    def interfaceParam(self, value):
        self._interfaceParam = value

    @property
    def skip(self):
        return self._skip

    @skip.setter
    def skip(self, value):
        self._skip = value

    @property
    def optional(self):
        return self._optional

    @optional.setter
    def optional(self, value):
        self._optional = value

    @property
    def ansibleValue(self):
        return self._ansibleValue

    @ansibleValue.setter
    def ansibleValue(self, value):
        self._ansibleValue = value

    @property
    def ignoreValForDelete(self):
        return self._ignoreValForDelete

    @ignoreValForDelete.setter
    def ignoreValForDelete(self, value):
        self._ignoreValForDelete = value

    @property
    def negateCommand(self):
        return self._negateCommand

    @negateCommand.setter
    def negateCommand(self, value):
        self._negateCommand = value

    @property
    def mergeAsReplace(self):
        return self._mergeAsReplace

    @mergeAsReplace.setter
    def mergeAsReplace(self, value):
        self._mergeAsReplace = value

    @property
    def translateMethod(self):
        return self._translateMethod

    @translateMethod.setter
    def translateMethod(self, value):
        self._translateMethod = value

    @property
    def exitCmd(self):
        return self._exitCmd

    @exitCmd.setter
    def exitCmd(self, value):
        self._exitCmd = value

    @property
    def ifParentValue(self):
        return self._ifParentValue

    @ifParentValue.setter
    def ifParentValue(self, value):
        self._ifParentValue = value

    @property
    def valueCheckMethod(self):
        return self._valueCheckMethod

    @valueCheckMethod.setter
    def valueCheckMethod(self, value):
        self._valueCheckMethod = value

    @property
    def ifFactsPresent(self):
        return self._ifFactsPresent

    @ifFactsPresent.setter
    def ifFactsPresent(self, value):
        self._ifFactsPresent = value

    @property
    def ifNextValue(self):
        return self._ifNextValue

    @ifNextValue.setter
    def ifNextValue(self, value):
        self._ifNextValue = value

    @property
    def parentName(self):
        return self._parentName

    @parentName.setter
    def parentName(self, value):
        self._parentName = value

    @property
    def noParam(self):
        return self._noParam

    @noParam.setter
    def noParam(self, value):
        self._noParam = value

    def dump(self):
        """
        @brief Print members of AnsibleWord class
        """
        log_vars(ansibleName=self.ansibleName, ansibleValue=self.ansibleValue,
                     listName=self.listName, listKeys=self.listKeys,
                     interfaceList=self.interfaceList, skip=self.skip,
                     listGroup=self.listGroup, interfaceParam=self.interfaceParam,
                     ignoreValForDelete=self.ignoreValForDelete,
                     negateCommand=self.negateCommand,
                     optional=self.optional, mergeAsReplace=self.mergeAsReplace,
                     translateMethod=self.translateMethod,
                     valueCheckMethod=self.valueCheckMethod,
                     ifFactsPresent=self.ifFactsPresent,
                     ifNextValue=self.ifNextValue,
                     parentName=self.parentName,
                     exitCmd=self.exitCmd, ifParentValue=self.ifParentValue,
                     noParam=self.noParam)


    def parse(self, word):
        """
        @brief Parse ansible word syntax and populate the current object
               Syntax:
               <token>&[more <token>]
               <token> : LIST:<ansible-list-node-name>
                         KEYS:<ansible-node-name>[|more <ansible-node-name>]
                         NAME:<ansible-node-name>
                         VALUE:<ansible-node-value>
                         INTERFACE_LIST
                         LIST_GROUP
                         INTERFACE_PARAM
                         SKIP
                         OPTIONAL
                         IGN_VAL_FOR_DEL
                         NEGATE_CMD:ALLOW|SKIP
                         MERGE_AS_REPLACE
                         TRANSLATE_METHOD:<method-name>
                         VALUE_CHECK_METHOD:<method-name>
                         IF_FACTS_PRESENT:<ansible-node-name>
                         PARENT_NAME:<ansible-node-name>
                         IF_NEXT_VAL:<next-token-index>@<next-token-value>
                         - <next-token-index> : 1 based index number
                         - <next-token-value> : EMPTY & NOT_EMPTY are used to presence of
                           a token value
                         EXIT_CMD:<exit-command>
                         IF_PARENT_VAL:<if-parent-val-conditions>
                         NO_PARAM - Indicates that respective cliName doesn't have any parameter

        @param word (str): ansible word content

        @returns None
        """
        if not word or not Constant.INDICATOR_ANSIBLE_WORD in word:
            return

        # Extract ansible word alone
        word = word.split(Constant.INDICATOR_ANSIBLE_WORD)[1]
        # Process based on Constant.DELIMITER_ANSIBLE_WORD
        word_parts = word.split(Constant.DELIMITER_ANSIBLE_WORD)
        log_vars(word_parts=word_parts)
        for word_part in word_parts:
            tokens = word_part.split(Constant.DELIMITER_ANSIBLE_WORD_TOKEN)
            log_vars(tokens=tokens)
            tokenType = tokens[0]
            # NAME:<ansible-node-name> - Name of ansible node
            if tokenType == Constant.NAME_INDICATOR:
                self.ansibleName = tokens[1]
            # LIST:<ansible-node-name>, Name of ansible node, type as list
            if tokenType == Constant.LIST_INDICATOR:
                self.listName = tokens[1]
            # INTERFACE_LIST - Indicates that list represents interfaces
            if tokenType == Constant.INTERFACE_LIST_INDICATOR:
                self.interfaceList = True
            # LIST_GROUP - Indicates that list represents group of individual commands
            if tokenType == Constant.LIST_GROUP_INDICATOR:
                self.listGroup = True
                self.listName = tokens[1]
            # KEYS:<ansible-node-name>[|<ansible-node-name>], List of key nodes
            if tokenType == Constant.KEYS_INDICATOR:
                self.listKeys = tokens[1]
            # INTERFACE_PARAM - Indicates that parameter represents interface name
            if tokenType == Constant.INTERFACE_PARAM_INDICATOR:
                self.interfaceParam = True
            # SKIP - Indicates that no ansible node to respective cli_word
            if tokenType == Constant.SKIP_INDICATOR:
                self.skip = Constant.SKIP_INDICATOR
            # OPTIONAL - Indicates that Parameter is optional
            if tokenType == Constant.OPTIONAL_INDICATOR:
                self.optional = True
            # VALUE - Indicates that respective cli_word is mapped to fixed ansible value
            if tokenType == Constant.VALUE_INDICATOR:
                self.ansibleValue = tokens[1]
            # IGN_VAL_FOR_DEL - Indicates that respective parameter value can be ignored for delete command
            if tokenType == Constant.IGN_VAL_FOR_DEL_INDICATOR:
                self.ignoreValForDelete = True
            # NEGATE_CMD - Indicates that negate command is applicable or not for this node
            if tokenType == Constant.NEGATE_CMD_INDICATOR:
                self.negateCommand = tokens[1]
            # MERGE_AS_REPLACE - Indicates that respective parameter supports merge as replace
            if tokenType == Constant.MERGE_AS_REPLACE:
                self.mergeAsReplace = True
            # TRANSLATE_METHOD - Translation method (b/w facts & config) name
            if tokenType == Constant.TRANSLATE_METHOD_INDICATOR:
                # TODO : Throw error when translate method is not present
                self.translateMethod = tokens[1]
            # VALUE_CHECK_METHOD - Method to check value of current node
            # while generating facts
            if tokenType == Constant.VALUE_CHECK_METHOD_INDICATOR:
                # TODO : Throw error when translate method is not present
                self.valueCheckMethod = tokens[1]
            # IF_FACTS_PRESENT - Check whether specific node is present in facts
            # while generating commands
            if tokenType == Constant.IF_FACTS_PRESENT_INDICATOR:
                self.ifFactsPresent = tokens[1]
            # PARENT_NAME - Indicates the ansible parent node of this node,
            # required to add child into optional unnamed parameter
            if tokenType == Constant.PARENT_NAME_INDICATOR:
                self.parentName = tokens[1]
            # EXIT_CMD - Translation method (b/w facts & config) name
            if tokenType == Constant.EXIT_CMD_INDICATOR:
                self.exitCmd = tokens[1]
            # IF_PARENT_VAL - Conditions to check whether parent has specific values
            # | is used as OR, * is used as wildcard
            if tokenType == Constant.IF_PARENT_VAL_INDICATOR:
                self.ifParentValue = tokens[1]
            # IF_NEXT_VAL - Conditions to check whether next node has specific values
            # | is used as OR, * is used as wildcard
            if tokenType == Constant.IF_NEXT_VAL_INDICATOR:
                self.ifNextValue = tokens[1]
            # NO_PARAM - Indicates that respective cliName doesn't have any parameter
            if tokenType == Constant.NO_PARAM_INDICATOR:
                self.noParam = True

class Facts(object):

   # Methods
    def __init__(self, wantOnly=None, diff=None, match=None, haveOnly=None,
                 compareObj=None):
        # Members
        if compareObj:
            self._wantOnly = compareObj.baseOnly
            self._diff = compareObj.diff
            self._match = compareObj.match
            self._haveOnly = compareObj.comparableOnly
        else:
            self._wantOnly = wantOnly
            self._diff = diff
            self._match = match
            self._haveOnly = haveOnly

    @property
    def wantOnly(self):
        return self._wantOnly

    @property
    def diff(self):
        return self._diff

    @property
    def match(self):
        return self._match

    @property
    def haveOnly(self):
        return self._haveOnly

    def isWantOnlyEmpty(self):
        return False if self.wantOnly else True

    def isMatchEmpty(self):
        return False if self.match else True

    def isDiffEmpty(self):
        return False if self.diff else True

    def isHaveOnlyEmpty(self):
        return False if self.haveOnly else True

    # Find node with given name
    # Locate the respective node in all types
    def find(self, name):
        result = None
        wantOnly = None
        match = None
        diff = None
        haveOnly = None

        if self.wantOnly:
            wantOnly = self.wantOnly.get(name, None)
        if self.diff:
            diff = self.diff.get(name, None)
        if self.match:
            match = self.match.get(name, None)
        if self.haveOnly:
            haveOnly = self.haveOnly.get(name, None)

        # log_vars(wantOnly=wantOnly, diff=diff, match=match, haveOnly=haveOnly)
        if wantOnly is None and diff is None and \
           match is None and haveOnly is None:
            return result

        result = Facts(wantOnly, diff, match, haveOnly)

        return result

    def dump(self):
        prettyJson = json.dumps(self.wantOnly, indent=4)
        log(f"wantOnly")
        log(f"{prettyJson}")
        prettyJson = json.dumps(self.match, indent=4)
        log(f"match")
        log(f"{prettyJson}")
        prettyJson = json.dumps(self.diff, indent=4)
        log(f"diff")
        log(f"{prettyJson}")
        prettyJson = json.dumps(self.haveOnly, indent=4)
        log(f"haveOnly")
        log(f"{prettyJson}")

class Node(object):

    # Methods
    def __init__(self, parent=None, cliName=None,
                 ansibleName=None, isRoot=False,
                 ansibleWord=None):
        # Defaults
        exitCmd = None
        ifParentValue = None
        negateCommand = None
        parentName = None
        ifNextValue = None

        # Read from ansibleWord
        if ansibleWord:
            exitCmd = ansibleWord.exitCmd
            ifParentValue = ansibleWord.ifParentValue
            negateCommand = ansibleWord.negateCommand
            ifNextValue = ansibleWord.ifNextValue
            parentName = ansibleWord.parentName

        # Members
        self._isRoot = isRoot
        self._cliName = cliName
        self._ansibleName = ansibleName
        self._exitCmd = exitCmd
        # Parent node
        self._parent = parent
        self._ifParentValue = ifParentValue
        # Next node (for mandatory parameter or nested list)
        self._next = None
        self._negateCommand = negateCommand
        self._ifNextValue = ifNextValue
        self._parentName = parentName
        self._optional = False
        # Children
        self._children = OrderedDict()

    @property
    def isRoot(self):
        return self._isRoot

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def cliName(self):
        return self._cliName

    @cliName.setter
    def cliName(self, value):
        self._cliName = value

    @property
    def ansibleName(self):
        return self._ansibleName

    @ansibleName.setter
    def ansibleName(self, value):
        self._ansibleName = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def next(self):
        return self._next

    @next.setter
    def next(self, value):
        self._next = value

    @property
    def exitCmd(self):
        return self._exitCmd

    @exitCmd.setter
    def exitCmd(self, value):
        self._exitCmd = value

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, value):
        self._children = value

    @property
    def ifParentValue(self):
        return self._ifParentValue

    @ifParentValue.setter
    def ifParentValue(self, value):
        self._ifParentValue = value

    @property
    def negateCommand(self):
        return self._negateCommand

    @property
    def ifNextValue(self):
        return self._ifNextValue

    @ifNextValue.setter
    def ifNextValue(self, value):
        self._ifNextValue = value

    @property
    def parentName(self):
        return self._parentName

    @parentName.setter
    def parentName(self, value):
        self._parentName = value

    @property
    def optional(self):
        return self._optional

    @optional.setter
    def optional(self, value):
        self._optional = value

    def buildKey(self):
        key = None

        # If ansibleName is available, prefer it
        if self.ansibleName:
            key = self.ansibleName
        elif self.cliName:
            key = self.cliName
        else: pass

        return key

    def addChild(self, key, obj):
        # For unnamed parameters, cliName will be None
        # So use ansibleName if key is None
        if not key:
            key = obj.ansibleName

        # Return the current object, if present already
        currObj = self.children.get(key, None)
        if not currObj:
            self.children.update({key: obj})

        return currObj

    def dumpChildren(self):
        if self.children:
            log(f"Children of {self.cliName}, {self.ansibleName}")
            for key, child in self.children.items():
                child.dump()

    def dump(self):
        """
        @brief Print members of Node class
        """
        # log(f"Node")
        log_vars(cliName=self.cliName, ansibleName=self.ansibleName)
        self.dumpChildren()

    def getParentCommandParts(self, reverse=False):
        # 1. Create temp command string parts
        commandParts = list()
        # 2. Get all parent nodes' cliName & append to command string parts
        parent = self.parent
        while parent:
            if parent.cliName:
                commandParts.append(parent.cliName)
            parent = parent.parent
        # 3. Reverse temp command string parts
        if reverse:
            commandParts.reverse()

        log_vars(commandParts=commandParts)
        return commandParts

    def createTreeNode(self, line, listGrpCache=None):
        """
        @brief Create tree node instance from line for Node class

        @param line (str): command line

        @returns newObj (instance): New object created or parent node
        @returns lineLeft (str): Line left after processing
        """
        newObj = None
        ansibleWordObj = None
        ansibleName = None
        cliName = None
        lineLeft = None

        # Return when line is empty
        if not line:
            log(f"line is empty")
            return newObj, lineLeft

        # 1. Split the string by SPACE with one occurance
        firstPart, lineLeft = splitLine(line, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
        cliName = firstPart
        ansibleName = firstPart

        # 2. Parse ansible word syntax if present
        if Constant.INDICATOR_ANSIBLE_WORD in firstPart:
            cliName = firstPart.split(Constant.INDICATOR_ANSIBLE_WORD)[0]
            ansibleWordObj = AnsibleWord(firstPart)
            ansibleName = ansibleWordObj.ansibleName
            ansibleWordObj.dump()

        # 4. Create node based on ansible word syntax
        if ansibleWordObj:
            # Skip node case
            if ansibleWordObj.skip:
                newObj = SkipNode(parent=self, cliName=cliName,
                                  ansibleWord=ansibleWordObj)
            # List node case
            elif ansibleWordObj.listName:
                if ansibleWordObj.interfaceList:
                    log(f"Create InterfaceListNode {cliName}, {ansibleWordObj.listName}")
                    # Interface list node case
                    newObj = InterfaceListNode(parent=self, cliName=cliName,
                                               ansibleWord=ansibleWordObj)
                elif ansibleWordObj.listGroup:
                    # Interface list node case
                    # Check and return the object if list group is already created
                    newObj = listGrpCache.get(ansibleWordObj.listName, None)
                    if not newObj:
                        log(f"Create ListGroupNode {cliName}, {ansibleWordObj.listName}")
                        newObj = ListGroupNode(parent=self, cliName=cliName,
                                               ansibleWord=ansibleWordObj)
                        listGrpCache.update({ansibleWordObj.listName: newObj})
                else:
                    log(f"Create ListNode {cliName}, {ansibleWordObj.listName}")
                    # If firstPart is parameter node, it shall be treated as
                    # key node and cliName for list shall be None
                    if isParamNode(firstPart):
                        cliName = None

                    # Normal list node case
                    newObj = ListNode(parent=self, cliName=cliName,
                                      ansibleWord=ansibleWordObj)

                    # If firstPart is parameter node, it shall be treated as
                    # key node and cliName for list shall be None
                    if isParamNode(firstPart):
                        paramPart = firstPart.split(Constant.INDICATOR_ANSIBLE_WORD)[0]
                        ansibleName = getParamName(paramPart)
                        keyNode = ParamNode(ansibleName=ansibleName)
                        newObj.addKeyNode(keyNode)

            # Fixed parameter node case
            elif ansibleWordObj.ansibleValue:
                log(f"Create FixedParamNode {cliName}, {ansibleWordObj.ansibleName}")
                newObj = FixedParamNode(parent=self, cliName=cliName,
                                        ansibleWord=ansibleWordObj)

            # NoParm case
            elif ansibleWordObj.noParam:
                log(f"Create Node {cliName} {ansibleName}")
                newObj = Node(parent=self, cliName=cliName, ansibleName=ansibleName)

            else: pass

        # Return if object is created in above step
        if newObj:
            return newObj, lineLeft

        # If the current token is Parameter Node, it is mandatory
        # (aka unnamed parameter node)
        if isParamNode(firstPart):
            ansibleName = getParamName(firstPart)
            if ansibleWordObj:
                paramPart = firstPart.split(Constant.INDICATOR_ANSIBLE_WORD)[0]
                ansibleName = getParamName(paramPart)

            # Interface parameter node case
            if ansibleWordObj and ansibleWordObj.interfaceParam:
                log(f"Create Unnamed InterfaceParamNode {ansibleName}")
                newObj = InterfaceParamNode(parent=self,
                                            ansibleName=ansibleName,
                                            ansibleWord=ansibleWordObj)
            else:
            # Unnamed parameter node case
                log(f"Create Unnamed ParamNode {ansibleName}")
                newObj = ParamNode(parent=self,
                                ansibleName=ansibleName,
                                ansibleWord=ansibleWordObj)
        # Return if object is created in above step
        if newObj:
            return newObj, lineLeft

        # 3. If the next token starts with PARAMETER_INDICATOR,
        #      create parameter node
        if isParamNode(lineLeft):
            # 3.1. Extract the ansibleName for the parameter
            #      Syntax: $<ansible-name>
            paramPart, lineLeft = splitLine(lineLeft, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
            ansibleName = getParamName(paramPart)
            if ansibleWordObj and ansibleWordObj.interfaceParam:
                log(f"Create InterfaceParamNode {cliName}, {ansibleName}")
                # Interface parameter node case
                newObj = InterfaceParamNode(parent=self, cliName=cliName,
                                            ansibleName=ansibleName,
                                            ansibleWord=ansibleWordObj)
            else:
                log(f"Create Named ParamNode {cliName}, {ansibleName}")
                # Normal parameter node case
                newObj = ParamNode(parent=self, cliName=cliName,
                                   ansibleName=ansibleName,
                                   ansibleWord=ansibleWordObj)

        # Return if object is created in above step
        if newObj:
            return newObj, lineLeft

        # 5. Create base node instance, if not other node types
        log(f"Create Node {cliName}, {ansibleName}")
        newObj = Node(parent=self, cliName=cliName, ansibleName=ansibleName)

        log_vars(lineLeft=lineLeft)

        return newObj, lineLeft

    def buildTree(self, line, listCache):
        """
        @brief Build tree based on line for Node class

        @param line (str): Command string
        @param listCache (dict): Placeholder to update all list nodes
                                 required for compress & expand facts

        @returns None
        """
        # Return when line is empty
        if not line:
            return

        # Generic buildTree implementation
        # 1. Create instance for first part of line parts
        newObj, lineLeft = self.createTreeNode(line)
        # 2. Append new node into children
        self.addChild(newObj.cliName, newObj)
        # 3. Invoke buildTree of new node with second part of line parts
        newObj.buildTree(lineLeft, listCache)

    def buildCmdsToSearch(self, commands):
        """
        @brief Build commands to search for while generating facts
               for Node class

        @param commands (list): Placeholder to update the command

        @returns None
        """
        # Generic buildCmdsToSearch implementation
        # For each child in children, invoke buildCmdsToSearch
        for key, child in self.children.items():
            child.buildCmdsToSearch(commands)

    # Check whether children nodes are present in facts dict or not
    def isChildPresent(self, facts):
        result = False
        # facts.dump()
        # 1. Iterate all subcommands
        for key, child in self.children.items():
            log(f"Check {child.cliName}, {child.ansibleName}")
            # SkipNode will not have ansibleName, so check it's the children
            if isinstance(child, SkipNode):
                result = child.isChildPresent(facts)
            else:
        # 1.1. Check whether facts node is present for subcommand
        # 1.2. If factsNode is present in wantOnly or match or diff,
        #      set result as False and break
                factsTmp = facts.find(child.ansibleName)
                if factsTmp and (factsTmp.wantOnly is not None or \
                                 factsTmp.match is not None or \
                                 factsTmp.diff is not None):
                    log(f"Child {child.ansibleName} is present")
                    result = True
            if result: break

        # log_vars(result=result)
        return result

    def createFactsNode(self, line, facts):
        """
        @brief Create facts node (if not present) instance from line
               for Node class

        @param line (str): command line
        @param facts (dict): Parent facts node where new node to be created

        @returns newObj (instance): New object created or parent node
        @returns lineLeft (str): Line left after processing
        """
        # Generic createFactsNode implementation
        newObj = None
        lineLeft = None

        log_vars(line=line, facts=facts)

        # Return when line is empty
        if not line:
            return newObj, lineLeft

        # 1. Split the line with DELIMITER_CLI_COMMAND_WORD by one occurance
        firstPart, lineLeft = splitLine(line, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
        # 2. Check whether firstPart is matching with cliName
        if firstPart != self.cliName:
            log(f"Failed to match {firstPart} & {self.cliName}")
            log_vars(newObj=newObj, lineLeft=lineLeft)
            return newObj, lineLeft
        # 3. Check facts node with matching current node's
        #    ansibleName, if so return facts node & lineLeft
        if self.ansibleName in facts:
            # If facts node already present, return the parent
            newObj = facts
            log_vars(newObj=newObj, lineLeft=lineLeft)
            return newObj, lineLeft
        # 4. If above is not true, create facts node with current node's
        #    ansibleName as key & dict as value
        newObj = {self.ansibleName: dict()}
        # 5. Add new node into facts
        facts.update(newObj)
        # 6. Return new node and lineLeft
        log_vars(newObj=newObj, lineLeft=lineLeft)
        return newObj, lineLeft

    def findMatchingChild(self, config, facts):
        """
        @brief Find matching child node from command string
               for Node class

        @param config (NetworkConfig or str): Config to be used for search
        @param config (str): Command string text

        @returns result (object): Matching subcommand node
        """
        # Generic findMatchingChild implementation
        result = None

        log_vars(config=config)

        # Return when config is empty
        if not config:
            return result

        # 1. Get command string text
        if isinstance(config, str):
            line = config
        else:
            line = config.text

        # 2. Iterate all child nodes
        for key, node in self.children.items():
            # Continue when node is processed already
            currentFacts = facts.get(self.ansibleName, None)
            if currentFacts and node.ansibleName in currentFacts:
                continue

            # Check whether cliName matches with line
            if node.validateCliName(line):
                log(f"Found child {node.cliName}, {node.ansibleName} by matching cliName")
                result = node
                break

        # 4. Return the result, if match is found
        return result

    # Validate cliName
    def validateCliName(self, line):
        result = False

        # Return True when cliName is empty, may be unnamed parameter
        if not self.cliName:
            result = True
        # Check whether child's key pattern is present in command string
        # Append SPACE with key pattern for exact match
        elif line.startswith(self.cliName + Constant.DELIMITER_CLI_COMMAND_WORD) or \
           line == self.cliName:
            result = True
        else: pass

        return result

    # Validate ifParentValue conditions
    def validateParentValue(self, facts):
        result = False
        if self.ifParentValue:
            # Get parent value
            parentVal = facts.get(self.parent.ansibleName, None)
            # TODO: Implement proper conditional validations
            # Skip the child, if present in facts already
            if parentVal and parentVal in self.ifParentValue:
                result = True

        log_vars(facts=facts, ifParentValue=self.ifParentValue, ansibleName=self.parent.ansibleName, result=result)
        return result

    # Validate ifNextValue conditions
    def validateNextValue(self, line):
        result = False
        nextValue = None
        lineLeft = line
        if self.ifNextValue:
            ifNextValueParts = self.ifNextValue.split(Constant.DELIMITER_IF_NEXT_VAL)
            tokenIndex = int(ifNextValueParts[0])
            tokenValueExpected = ifNextValueParts[1]
            tokens = line.split(Constant.DELIMITER_CLI_COMMAND_WORD)
            if len(tokens) >= tokenIndex:
                tokenValueCurrent = tokens[tokenIndex-1]
            else:
                tokenValueCurrent = None
            if tokenValueCurrent:
                if tokenValueExpected == Constant.NOT_EMPTY_INDICATOR or \
                   tokenValueExpected == tokenValueCurrent:
                    result = True
            else:
                if tokenValueExpected == Constant.EMPTY_INDICATOR:
                    result = True
            log_vars(tokenValueCurrent=tokenValueCurrent, tokenValueExpected=tokenValueExpected)

        log_vars(line=line, ifNextValue=self.ifNextValue, result=result)
        return result

    def generateFacts(self, config, facts, listGrpCache=None):
        """
        @brief Generate facts from the config for Node class

        @param config (NetworkConfig): Configurations to be converted as facts
        @param facts (dict): Placeholder to update the facts

        @returns None
        """
        # Generic generateFacts implementation
        currFactsNode = None
        lineLeft = None
        # 1. Call createFactsNode
        currFactsNode, lineLeft = self.createFactsNode(config, facts)
        log_vars(currFactsNode=currFactsNode)
        currFactsNodeVal = currFactsNode.get(self.ansibleName, None)
        # 2. Return when lineLeft is empty
        if not lineLeft:
            return
        # 3. Find matching node with next token in children
        child = self.findMatchingChild(lineLeft, facts)
        log_vars(child=child)
        if child:
        # 4. Call generateFacts() with matching child with lineLeft
            lineLeft = child.generateFacts(lineLeft, currFactsNodeVal,
                                           listGrpCache=listGrpCache)

        return lineLeft

    def generateCommandParts(self, parentFacts, currentFacts, state,
                             grantParentFacts=None,
                             includeParentPart=False):
        """
        @brief Generate config from the facts for Node class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        @returns None
        """
        # Generic implementation of generateCommandParts
        # Create temp command string parts
        commandParts = list()

        log_vars(parentFacts=parentFacts, currentFacts=currentFacts)

        # Return when no ansibleName is found
        currentFactsTmp = currentFacts.get(self.ansibleName, None)
        if not currentFactsTmp:
            return commandParts

        # Iterate all childs and invoke generateCommandParts
        for key, child in self.children.items():
            commandPartsTmp = child.generateCommandParts(currentFactsTmp, currentFactsTmp, state)
            if commandPartsTmp:
                commandPartsTmp.insert(0, self.cliName)
                commandParts.append(commandPartsTmp)

        return commandParts

    def generateMergeCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : merged)
               for Node class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        @returns None
        """
        # Generic implementation of generateMergeCommands
        # 1. If children is present, iterate all children
        if self.children:
            for key, child in self.children.items():
                # SkipNode will not have ansibleName, so call generate method
                # to process subsequent fact nodes inside SkipNode children
                if isinstance(child, SkipNode) and \
                   not child.ansibleName:
                    child.generateMergeCommands(parentFacts, currentFacts,
                                                parentCommand, config)
                    continue
        #   1.1. Call find with ansibleName
                factsNode = currentFacts.find(child.ansibleName)
        #   1.2. Call generateMergeCommands for respective child
                if factsNode:
                    log(f"Processing {child.ansibleName}")
                    child.generateMergeCommands(currentFacts, factsNode,
                                                parentCommand, config)
        else:
            # TODO: Throw error
            log(f"Unexpected error. Node has empty children")

    def generateDeleteCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : deleted)
               for Node class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        @returns None
        """
        # Generic implementation of generateDeleteCommands
        # 1. If children is present, iterate all children
        if self.children:
            for key, child in self.children.items():
                # SkipNode will not have ansibleName, so call generate method
                # to process subsequent fact nodes inside SkipNode children
                if isinstance(child, SkipNode) and \
                   not child.ansibleName:
                    child.generateDeleteCommands(parentFacts, currentFacts,
                                                parentCommand, config)
                    continue
        #   1.1. Call find with ansibleName
        #    1.1 Locate facts node with ansibleName
                factsNode = currentFacts.find(child.ansibleName)
        #    1.2 Call generateDeleteCommands with above facts node
                if factsNode:
                    log(f"Processing {child.ansibleName}")
                    child.generateDeleteCommands(currentFacts, factsNode, parentCommand, config)
        # 2. If children is not present,
        else:
            # TODO: Throw error
            log(f"Unexpected error. Node has empty children")

    def generateDeleteAllCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : deleted)
               for Node class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        @returns None
        """
        # Generic implementation of generateDeleteAllCommands
        # 1. If children is present, iterate all children
        if self.children:
            for key, child in self.children.items():
                # SkipNode will not have ansibleName, so call generate method
                # to process subsequent fact nodes inside SkipNode children
                if isinstance(child, SkipNode) and \
                   not child.ansibleName:
                    child.generateDeleteAllCommands(parentFacts, currentFacts,
                                                parentCommand, config)
                    continue
        #   1.1. Call find with ansibleName
        #    1.1 Locate facts node with ansibleName
                factsNode = currentFacts.find(child.ansibleName)
        #    1.2 Call generateDeleteAllCommands with above facts node
                if factsNode:
                    log(f"Processing {child.ansibleName}")
                    child.generateDeleteAllCommands(config, factsNode,
                                                    parentCommand, config)
        # 2. If children is not present,
        else:
            # TODO: Throw error
            log(f"Unexpected error. Node has empty children")

    def generateReplaceCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : replaced)
               for Node class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config
                             both old & new config are included

        @returns None
        """
        # Generic implementation of generateReplaceCommands
        # 1. If children is present, iterate all children
        if self.children:
            for key, child in self.children.items():
                # SkipNode will not have ansibleName, so call generate method
                # to process subsequent fact nodes inside SkipNode children
                if isinstance(child, SkipNode) and \
                   not child.ansibleName:
                    child.generateReplaceCommands(parentFacts, currentFacts,
                                                parentCommand, config)
                    continue
        #   1.1. Call find with ansibleName
        #    1.1 Locate facts node with ansibleName
                factsNode = currentFacts.find(child.ansibleName)
        #    1.2 Call generateReplaceCommands with above facts node
                if factsNode:
                    log(f"Processing {child.ansibleName}")
                    child.generateReplaceCommands(currentFacts, factsNode, parentCommand, config)
        # 2. If children is not present, Throw exception
        else:
            # TODO: Throw exception & add log
            log(f"Unexpected error. Node has empty children")

    def generateOverriddenCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : overridden)
               for Node class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config
                             both old & new config are included

        @returns None
        """
        # Generic implementation of generateReplaceCommands
        # 1. If children is present, iterate all children
        if self.children:
            for key, child in self.children.items():
                # SkipNode will not have ansibleName, so call generate method
                # to process subsequent fact nodes inside SkipNode children
                if isinstance(child, SkipNode) and \
                   not child.ansibleName:
                    child.generateOverriddenCommands(parentFacts, currentFacts,
                                                parentCommand, config)
                    continue
        #   1.1. Call find with ansibleName
        #    1.1 Locate facts node with ansibleName
                factsNode = currentFacts.find(child.ansibleName)
                if factsNode:
                    log(f"Processing {child.ansibleName}")
        #    1.2 Call generateReplaceCommands with above facts node
                    child.generateOverriddenCommands(currentFacts, factsNode, parentCommand, config)
        # 2. If children is not present, Throw exception
        else:
            # TODO: Throw exception & add log
            log(f"Unexpected error. Node has empty children")

    def generateExitCmd(self, parentCommand, config):
        """
        @brief Generate exit command

        @param config (NetworkConfig): Placeholder to append config

        @returns None
        """
        # Return when parentCommand is empty
        if not parentCommand:
            return

        if self.exitCmd:
            addToConfig(config, self.exitCmd, parentCommand)

# Parameter node
class ParamNode(Node):

    # Methods
    def __init__(self, parent=None, cliName=None,
                 ansibleName=None, ansibleWord=None):
        # Defaults
        mergeAsReplace = True
        ignoreValForDelete = False
        optional = False
        translateMethod = None
        valueCheckMethod = None
        ifNextValue = None
        parentName = None
        ifParentValue = None
        ifFactsPresent = None
        negateCommand = None

        # Extract values from ansibleWord, if passed
        if ansibleWord:
            mergeAsReplace = ansibleWord.mergeAsReplace
            ignoreValForDelete = ansibleWord.ignoreValForDelete
            optional = ansibleWord.optional
            translateMethod = ansibleWord.translateMethod
            valueCheckMethod = ansibleWord.valueCheckMethod
            ifNextValue = ansibleWord.ifNextValue
            parentName = ansibleWord.parentName
            ifFactsPresent = ansibleWord.ifFactsPresent
            ifParentValue = ansibleWord.ifParentValue
            negateCommand = ansibleWord.negateCommand

        super().__init__(parent=parent, cliName=cliName,
                         ansibleName=ansibleName,
                         ansibleWord=ansibleWord)
        # Use super().next as unnamed parameter (aka mandatory)

        # Members
        self._ignoreValForDelete = ignoreValForDelete
        self._mergeAsReplace = mergeAsReplace
        self._translateMethod = translateMethod
        self._valueCheckMethod = valueCheckMethod
        self._ifFactsPresent = ifFactsPresent
        # All named parameters are treated as optional
        if self.cliName:
            self.optional = True
        else:
            # For positional parameter, option need to be expicitly set
            self.optional = optional
        # super().children as named parameter based commands

    @property
    def ignoreValForDelete(self):
        return self._ignoreValForDelete

    @ignoreValForDelete.setter
    def ignoreValForDelete(self, value):
        self._ignoreValForDelete = value

    @property
    def mergeAsReplace(self):
        return self._mergeAsReplace

    @mergeAsReplace.setter
    def mergeAsReplace(self, value):
        self._mergeAsReplace = value

    @property
    def translateMethod(self):
        return self._translateMethod

    @translateMethod.setter
    def translateMethod(self, value):
        self._translateMethod = value

    @property
    def valueCheckMethod(self):
        return self._valueCheckMethod

    @valueCheckMethod.setter
    def valueCheckMethod(self, value):
        self._valueCheckMethod = value

    @property
    def ifFactsPresent(self):
        return self._ifFactsPresent

    @ifFactsPresent.setter
    def ifFactsPresent(self, value):
        self._ifFactsPresent = value

    def dump(self):
        """
        @brief Print members of ParamNode class
        """
        # log(f"ParamNode")
        log_vars(cliName=self.cliName, ansibleName=self.ansibleName,
                     ignoreValForDelete=self.ignoreValForDelete,
                     mergeAsReplace=self.mergeAsReplace,
                     optional=self.optional,
                     translateMethod=self.translateMethod,
                     valueCheckMethod=self.valueCheckMethod,
                     ifFactsPresent=self.ifFactsPresent,
                     ifNextValue=self.ifNextValue,
                     parentName=self.parentName,
                     ifParentValue=self.ifParentValue)
        self.dumpChildren()
        if self.next:
            log(f"Next of {self.cliName}, {self.ansibleName}")
            self.next.dump()

    # Get ansible value from command line
    def getAnsibleValue(self, line):
        value = None
        lineLeft = None

        if isinstance(line,str):
            if line.startswith(Constant.DOUBLE_QUOTE_CHAR): # Quoted string as value
                value = re.findall(r'"([^"]*)"', line)[0]
                _, lineLeft = splitLine(line, Constant.DELIMITER_CLI_COMMAND_WORD, 2)
            else:
                value, lineLeft = splitLine(line, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
        elif isinstance(line, enumerate):
            token= next(line, None)
            value = token[1]
        else:
            log(f"Unknown instance type")

        # Call translate if mentioned
        if value and self.translateMethod:
            value = translate(self.translateMethod, value,
                              ConvUtilsConstant.CONFIG_TO_FACTS)

        return value, lineLeft

    def buildTree(self, line, listCache):
        """
        @brief Build tree based on line for ParamNode class

        @param line (str): Command string
        @param listCache (dict): Placeholder to update all list nodes
                                 required for compress & expand facts

        @returns None
        """
        # Return when line is empty
        if not line:
            return

        # Create tree node
        newObj, lineLeft = self.createTreeNode(line)
        # If newObj is not optional parameter or not based on parent value,
        # continue buildTree for newObj
        if not newObj.optional and not newObj.ifParentValue:
            log(f"Added {newObj.cliName}, {newObj.ansibleName} as next of {self.cliName}, {self.ansibleName}")
            self.next = newObj
            lineLeft = self.next.buildTree(lineLeft, listCache)
        else:
            # Continue till locating named parameter node
            while (newObj.optional or newObj.ifParentValue):
                key = newObj.buildKey()
                self.addChild(key, newObj)
                log(f"Added {newObj.cliName}, {newObj.ansibleName} as child of {self.cliName}, {self.ansibleName}")
                # Break the loop when either next node is not a optional
                # parameter node or not based on parent value or
                # line is empty
                if not lineLeft or (not hasOptional(lineLeft) and \
                                    not hasIfParentVal(lineLeft)):
                    break
                newObj, lineLeft = self.createTreeNode(lineLeft)

        # Call buildTree if manadatory parameter
        if lineLeft and not newObj.optional:
            log(f"Added {newObj.cliName}, {newObj.ansibleName} as next of {self.cliName}, {self.ansibleName}")
            self.next = newObj
            lineLeft = self.next.buildTree(lineLeft, listCache)

        return lineLeft

    def buildCmdsToSearch(self, commands):
        """
        @brief Build commands to search for while generating facts
               for ParamNode class

        @param commands (list): Placeholder to update the command

        @returns None
        """
        # 1. Form temp list
        commandParts = list()
        # 2. Append cliName of current node to temp list
        commandParts.append(self.cliName)
        # 3. Traverse back with parent node till root node
        #    and append cliName of parent nodes to temp list
        parentParts = self.getParentCommandParts()
        commandParts.extend(parentParts)
        # 4. Reverse the list
        commandParts.reverse()
        # 5. Form command by joining all items with DELIMITER_CLI_COMMAND_WORD
        command = convertToCommand(commandParts)
        # 6. Append formed cmdPattern to commands argument
        commands.append(command)

    def findMatchingChild(self, config, facts, visitedNodes):
        """
        @brief Find matching child node from command string
               for ParamNode class

        @param config (NetworkConfig or str): Config to be used for search
        @param config (str): Command string text
        @param facts (dict): Facts generated so far

        @returns result (object): Matching subcommand node
        """
        # Generic findMatchingChild implementation
        result = None

        log_vars(config=config)

        # Return when config is empty
        if not config:
            return result

        # 1. Get command string text
        if isinstance(config, str):
            line = config
        else:
            line = config.text
        # 2. Iterate all child nodes
        for key, node in self.children.items():
            # Continue when node is processed already
            if node in visitedNodes:
                continue
            else:
                # Add the current node to visitedNodes
                visitedNodes.append(node)

            # Check ifNextValue condition is met
            if node.validateNextValue(line):
                log(f"Found child {node.cliName}, {node.ansibleName} by matching ifNextValue")
                result = node

            # Continue to next node if child not meeting the ifNextValue condition
            if node.ifNextValue and not result: continue

            # Check whether ifFactsPresent condition is met
            if node.validateFactsPresent(facts):
                log(f"Found child {node.cliName}, {node.ansibleName} by matching {node.ifFactsPresent}")
                result = node

            # Continue to next node if child not meeting the ifFactsPresent condition
            if node.ifFactsPresent and not result: continue

            # Check ifParentValue condition is met
            if node.validateParentValue(facts) and \
               node.ansibleName not in facts:
                log(f"Found child {node.cliName}, {node.ansibleName} by matching ifParentValue")
                result = node
                # Break when child's cliName is empty, otherwise it will go through next check
                if not node.cliName: break

            # Continue to next node if child not meeting the ifParentValue condition
            if node.ifParentValue and not result: continue

            # Break when result is true to avoid matching against cliName
            # This is required in order to validate multiple conditions on a node
            if result: break

            # Check whether cliName matches with line
            if node.validateCliName(line):
                log(f"Found child {node.cliName}, {node.ansibleName} by matching cliName")
                result = node
                break

        # 4. Return the result, if match is found
        return result

    # Validate ifFactsPresent conditions
    def validateFactsPresent(self, facts):
        """
        @brief Validate ifFactsPresent conditions

        @param facts (dict): Facts dictionary

        @returns True if validation passes, False otherwise
        """
        result = False
        negateFlag = False

        if self.ifFactsPresent:
            if self.ifFactsPresent.startswith(ValueCheckConstant.NEGATE_CHAR):
                name = self.ifFactsPresent.split(ValueCheckConstant.NEGATE_CHAR, 1)[1]
                negateFlag = True
            else:
                name = self.ifFactsPresent

            if facts.get(name, None):
                result = True

            if negateFlag:
                result = not result

        log_vars(ifFactsPresent=self.ifFactsPresent, result=result)
        return result
 
    def createFactsNode(self, line, facts):
        """
        @brief Create facts node (if not present) instance from line
               for ParamNode class

        @param line (str): command line
        @param facts (dict): Parent facts node where new node to be created

        @returns newObj (instance): New object created or parent node
        @returns lineLeft (str): Line left after processing
        """
        newObj = None
        lineLeft = line

        log_vars(line=line, facts=facts)

        # Return when line is empty
        if not line:
            return newObj, lineLeft

        if self.cliName and \
           not line.startswith(self.cliName + Constant.DELIMITER_CLI_COMMAND_WORD) and \
           line != self.cliName:
            log(f"No matching node for {self.cliName}")
            # TODO: Throw error
            return newObj, lineLeft

        # 3. Check facts node with matching current node's
        #    ansibleName, if so print error and return
        if self.ansibleName in facts:
            log(f"Facts node for {self.ansibleName} exists already")
            # TODO: Throw error
            return newObj, lineLeft

        # 1. Split the line with DELIMITER_CLI_COMMAND_WORD by one occurance
        # 2. For named parameter, check whether firstPart is matching
        # with cliName
        # 4. If above is not true, create facts node with current node's
        #    ansibleName as key & next token as value
        if self.cliName:
            _, lineLeft = splitLine(lineLeft, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
        ansibleValue, lineLeft = self.getAnsibleValue(lineLeft)

        # Validate whether condition is satisfied before generating facts
        if self.valueCheckMethod:
            if not validate(self.valueCheckMethod, ansibleValue):
                log(f"Validation for {ansibleValue} failed against {self.valueCheckMethod} for {self.ansibleName}")
                # Return original input to caller
                lineLeft = line
                return newObj, lineLeft

        newObj = {self.ansibleName: ansibleValue}
        # 5. Add new node into facts
        facts.update(newObj)
        # 6. Return new node and lineLeft
        log_vars(newObj=newObj, lineLeft=lineLeft)
        return newObj, lineLeft

    def generateFacts(self, line, facts, listGrpCache=None):
        """
        @brief Generate facts from the config for ParamNode class

        @param line (str): Configuration to be converted as facts
        @param facts (dict): Placeholder to update the facts

        @returns line_left (str): Remaining line from config
        """
        visitedNodes = list()

        # 1. Call createFactsNode, expected to return newObj
        obj, lineLeft = self.createFactsNode(line, facts)

        # Return when failed to create node
        if not obj:
            return lineLeft

        # 2. Return when lineLeft is empty
        if not lineLeft:
            return lineLeft

        # 3. Generate facts for all children
        child = self.findMatchingChild(lineLeft, facts, visitedNodes)
        while child:
            log_vars(child=child)
        # 4. Call generateFacts() with matching child with lineLeft
            lineLeft = child.generateFacts(lineLeft, facts)
            child = self.findMatchingChild(lineLeft, facts, visitedNodes)

            # 2. Break when lineLeft is empty
            if not lineLeft: break

        # 2. Return when lineLeft is empty
        if not lineLeft:
            return lineLeft

        # Call generateFacts for next node if present
        if self.next:
            lineLeft = self.next.generateFacts(lineLeft, facts)

        return lineLeft

    # Get command value from facts & state
    def getCommandValue(self, facts, state):
        result = False
        value = None
        factsNode = None
        # log(f"facts")
        # if isinstance(facts, Facts):
        #     facts.dump()
        # log_vars(facts=facts)
        log_vars(state=state)
        # 2. Get the value of facts node
        # 2.1. For merge state,
        if state == Constant.STATE_MERGED or \
           state == Constant.STATE_REPLACED:
            if isinstance(facts, Facts):
                # 1. Locate facts node in wantOnly
                if facts.wantOnly is not None:
                    factsNode = facts.wantOnly
                # 2. If above is None, locate factsNode in diff
                elif facts.diff is not None:
                    factsNode = facts.diff
                # 3. If above is None, return
                else:
                    log(f"Node is not present in wantOnly & diff")
                    return result, value
            elif isinstance(facts, dict):
                factsNode = facts.get(self.ansibleName, None)
            else:
                factsNode = facts

            log_vars(factsNode=factsNode)
            # 2.1.1. Merge as part of replace, so extract new value
            if isinstance(factsNode, dict):
                value = factsNode.get(Constant.BASE_VAL_STR, None)
            # 2.1.2. Normal merge, so treat current node as value
            else:
                value = factsNode
        # 2.2. For delete state,
        else:
            if isinstance(facts, Facts):
                if facts.match is not None:
                    factsNode = facts.match
                # 3. If above is None, return
                else:
                    log(f"Node is not present in match")
                    return result, value
            elif isinstance(facts, dict):
                factsNode = facts.get(self.ansibleName, None)
            else:
                factsNode = facts

            log_vars(factsNode=factsNode)
            if isinstance(factsNode, dict):
                value = factsNode.get(Constant.COMPARABLE_VAL_STR, None)
            else:
                value = factsNode
            # 2.2.1. Reset value if IGNORE_VAL_FOR_DELETE is set
            if value and self.ignoreValForDelete:
                value = None
                result = True

        # 3. Call translate if available
        if value is not None:
            result = True
            if self.translateMethod:
                value = translate(self.translateMethod, value,
                                  ConvUtilsConstant.FACTS_TO_CONFIG)

        # Add quotes for multi-word string
        if isinstance(value, str) and \
           Constant.DELIMITER_CLI_COMMAND_WORD in value:
            value = Constant.DOUBLE_QUOTE_CHAR + value + \
                    Constant.DOUBLE_QUOTE_CHAR

        # log_vars(result=result, value=value)
        # 4. Return
        return result, value

    def generateCommandValue(self, commandParts, factsNode, state):
        result = True
        # 2.2 Call getCommandValue with facts node & append to command string parts
        result, commandValue = self.getCommandValue(factsNode, state)
        log_vars(commandValue=commandValue)

        if commandValue is not None:
            commandParts.append(commandValue)

        # log_vars(commandParts=commandParts)
        return result

    def generateCommandParts(self, parentFacts, currentFacts, state,
                             grantParentFacts=None,
                             includeParentPart=False):
        """
        @brief Generate config from the facts (state : merged)
               for ParamNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        @returns None
        """
        # 1. Create temp command string parts
        commandParts = list()

        # if isinstance(parentFacts, Facts):
        #     log(f"parentFacts")
        #     parentFacts.dump()
        # if isinstance(currentFacts, Facts):
        #     log(f"currentFacts")
        #     currentFacts.dump()
        # log_vars(parentFacts=parentFacts, currentFacts=currentFacts)
        # 5. Iterate all parent nodes
        if self.ifFactsPresent and not self.validateFactsPresent(parentFacts):
            return commandParts

        if includeParentPart:
            parentParts = self.getParentCommandParts(reverse=True)
            commandParts.extend(parentParts)
        # 4. Append cliName of current node to command string parts
        log(f"Processing current node {self.ansibleName}")
        if self.cliName:
            commandParts.append(self.cliName)
        if not self.generateCommandValue(commandParts, currentFacts, state):
            commandParts = None
            return commandParts

        # For deleted state, if the current parameter value is ignored,
        # then no need to proceed generating parts for children and next node.
        if state == Constant.STATE_DELETED and self.ignoreValForDelete:
            log_vars(commandParts=commandParts)
            return commandParts

        # 2. For each children
        for key, child in self.children.items():
            log(f"Processing child node {child.cliName}, {child.ansibleName}")
            # Append cliName directly for SkipNode
            if isinstance(child, SkipNode):
                commandParts.append(child.cliName)
            else:
                factsTmp = None
                if isinstance(parentFacts, Facts):
                    factsTmp = parentFacts.find(child.ansibleName)
                elif isinstance(parentFacts, dict):
                    factsTmp = parentFacts.get(child.ansibleName, None)
                else: pass

                if factsTmp is not None:
                    commandPartsTmp = child.generateCommandParts(parentFacts,
                                                                 factsTmp,
                                                                 state)
                    if commandPartsTmp:
                        commandParts.extend(commandPartsTmp)

        # 6. Generate command parts for next node and append
        if self.next:
            log(f"Processing next node {self.next.ansibleName}")
            factsTmp = None
            commandPartsTmp = None
            if isinstance(parentFacts, Facts):
                factsTmp = parentFacts.find(self.next.ansibleName)
            elif isinstance(parentFacts, dict):
                factsTmp = parentFacts.get(self.next.ansibleName, None)
            else: pass

            if factsTmp:
                commandPartsTmp = self.next.generateCommandParts(parentFacts,
                                                                 factsTmp,
                                                                 state,
                                                                 grantParentFacts=grantParentFacts)
            # If the next node is mandatory parameter, it will be available
            # in either match, diff or haveOnly of grantParentFacts
            if not commandPartsTmp and not self.next.optional and \
               grantParentFacts:
                log(f"Attempting to generateCommand from grantParentFacts for {self.next.ansibleName}")
                if grantParentFacts.diff is not None:
                    factsTmp = grantParentFacts.diff.get(self.next.ansibleName, None)
                if not factsTmp and grantParentFacts.match is not None:
                    factsTmp = grantParentFacts.match.get(self.next.ansibleName, None)
                if not factsTmp and grantParentFacts.haveOnly is not None:
                    factsTmp = grantParentFacts.haveOnly.get(self.next.ansibleName, None)

                if factsTmp:
                    commandPartsTmp = self.next.generateCommandParts(parentFacts,
                                                                 factsTmp,
                                                                 state,
                                                                 grantParentFacts=grantParentFacts)
            if commandPartsTmp:
                commandParts.extend(commandPartsTmp)

        log_vars(commandParts=commandParts)
        return commandParts

    def generateMergeCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : merged)
               for ParamNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        @returns None
        """
        # 1. Create temp command string parts
        commandParts = self.generateCommandParts(parentFacts, currentFacts,
                                                 Constant.STATE_MERGED,
                                                 includeParentPart=True)
        # 7. Join command string parts with SPACE
        command = convertToCommand(commandParts)
        log_vars(command=command)
        # 8. Add to Config
        addToConfig(config, command, parentCommand)

    def generateDeleteCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : deleted)
               for ParamNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        """
        # 1. Create temp command string parts
        commandParts = self.generateCommandParts(parentFacts, currentFacts,
                                                 Constant.STATE_DELETED,
                                                 includeParentPart=True)

        # 6. Append "no" keyword to the temp command string parts
        # Skip negateCommand for FixedParamNode instance as it is handled
        # inside the FixedParamNode class itself
        if not isinstance(self, FixedParamNode):
            negateCommand(commandParts)

        # 7. Join command string parts with SPACE
        command = convertToCommand(commandParts)
        log_vars(command=command)
        # 8. Add to Config
        addToConfig(config, command, parentCommand)

    def generateDeleteAllCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : deleted)
               for ParamNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        """
        # Generete delete for haveOnly
        factsTmp = Facts(None, None, currentFacts.haveOnly, None)
        self.generateDeleteCommands(parentFacts, factsTmp, parentCommand, config)

    def generateReplaceCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : replaced)
               for ParamNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config
                             both old & new config are included

        @returns None
        """
        log(f"Processing {self.ansibleName}")
        # Return when currentFacts is empty
        if not currentFacts:
            return

        # 3. Skip match only node
        if currentFacts.wantOnly is None and currentFacts.diff is None and \
           currentFacts.haveOnly is None and currentFacts.match is not None:
            return

        # 3. Delete haveOnly node
        if currentFacts.wantOnly is None and currentFacts.diff is None and \
           currentFacts.match is None and currentFacts.haveOnly is not None:
            factsTmp = Facts(None, None, currentFacts.haveOnly, None)
            self.generateDeleteCommands(currentFacts, factsTmp, parentCommand, config)
            return

        # 1. If mergeAsReplace is True,
        if self.mergeAsReplace:
        #    1.1 Call generateMergeCommands with new config
            self.generateMergeCommands(parentFacts, currentFacts, parentCommand, config)
        # 2. If mergeAsReplace is False,
        else:
        #    2.1 Call generateDeleteCommands with old config
            self.generateDeleteCommands(parentFacts, currentFacts, parentCommand, config)
        #    2.2 Call generateMergeCommands with new config
            self.generateMergeCommands(parentFacts, currentFacts, parentCommand, config)

    def generateOverriddenCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : overridden)
               for ParamNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config
                             both old & new config are included

        @returns None
        """
        self.generateReplaceCommands(parentFacts, currentFacts, parentCommand, config)

# Fixed Parameter node
class FixedParamNode(ParamNode):

    # Methods
    def __init__(self, parent=None, cliName=None,
                 ansibleWord = None):
        super().__init__(parent=parent, cliName=cliName,
                         ansibleName=ansibleWord.ansibleName,
                         ansibleWord=ansibleWord)
        # Members
        # super().children as next token based commands
        self._ansibleValue = ansibleWord.ansibleValue

    @property
    def ansibleValue(self):
        return self._ansibleValue

    @ansibleValue.setter
    def ansibleValue(self, value):
        self._ansibleValue = value

    def dump(self):
        """
        @brief Print members of FixedParamNode class
        """
        # log(f"FixedParamNode")
        log_vars(cliName=self.cliName, ansibleName=self.ansibleName,
                 ansibleValue=self.ansibleValue,
                 ifParentValue=self.ifParentValue,
                 ifNextValue=self.ifNextValue,
                 parentName=self.parentName,
                 optional=self.optional,
                 valueCheckMethod=self.valueCheckMethod,
                 ifFactsPresent=self.ifFactsPresent,
                 negateCommand=self.negateCommand)
        self.dumpChildren()

    def getAnsibleValue(self, line):
        # 1. Return fixed ansibleValue
        return self.ansibleValue

    # buildTree not to be overridden
    # buildCmdsToSearch not to be overridden

    def createFactsNode(self, line, facts):
        """
        @brief Create facts node (if not present) instance from line
               for FixedParamNode class

        @param line (str): command line
        @param facts (dict): Parent facts node where new node to be created

        @returns newObj (instance): New object created or parent node
        @returns lineLeft (str): Line left after processing
        """
        newObj = None
        lineLeft = line

        log_vars(line=line, facts=facts)

        # Return when line is empty
        if not line:
            return newObj, lineLeft

        # 3. Check facts node with matching current node's
        #    ansibleName, if so print error and return
        if self.ansibleName in facts:
            # TODO: Throw error
            return newObj, lineLeft

        # 1. Split the line with DELIMITER_CLI_COMMAND_WORD by one occurance
        firstPart, lineLeft = splitLine(line, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
        # 2. Check whether firstPart is matching with cliName
        if firstPart != self.cliName:
            # TODO: Throw error
            return newObj, lineLeft

        # Validate whether condition is satisfied before generating facts
        if self.valueCheckMethod:
            if not validate(self.valueCheckMethod, self.ansibleValue):
                log(f"Validation for {self.ansibleValue} failed against {self.valueCheckMethod} for {self.ansibleName}")
                # Return original input to caller
                lineLeft = line
                return newObj, lineLeft

        # 4. If above is not true, create facts node with current node's
        #    ansibleName as key & ansibleValue as value
        newObj = {self.ansibleName: self.ansibleValue}
        # 5. Add new node into facts
        facts.update(newObj)
        # 6. Return new node and lineLeft
        return newObj, lineLeft

    def addNegateCommand(self, value, commandParts, state):
        negateFlag = False
        # log_vars(value=value, ansibleValue=self.ansibleValue, state=state,
        #          negateCommand=self.negateCommand,
        #          commandParts=commandParts)
        if self.negateCommand:
            if self.negateCommand == Constant.NEGATE_CMD_ALLOW:
            # For deleted state, if command value is same as in object, delete case
            # otherwise merge case
                if state == Constant.STATE_DELETED:
                    if value is strToBool(self.ansibleValue):
                        negateFlag = True
            # For merged state, if command value is same as in object, merge case
            # otherwise delete case
                else:
                    if value is not strToBool(self.ansibleValue):
                        negateFlag = True
            # For SKIP negateCommand, add negate for deleted state alone
            elif self.negateCommand == Constant.NEGATE_CMD_SKIP:
                if state == Constant.STATE_DELETED:
                    if value is strToBool(self.ansibleValue):
                        negateFlag = True
            else: pass

        # Skip negate flag for current node if parent node handles negation
        if self.parent and self.parent.negateCommand:
            negateFlag = False

        if negateFlag:
            negateCommand(commandParts)

        return

    def generateCommandParts(self, parentFacts, currentFacts, state,
                             grantParentFacts=None,
                             includeParentPart=False):
        """
        @brief Generate config from the facts (state : merged)
               for FixedParamNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        @returns None
        """
        # 1. Create temp command string parts
        commandParts = list()

        # if isinstance(parentFacts, Facts):
        #     log(f"parentFacts")
        #     parentFacts.dump()
        # if isinstance(currentFacts, Facts):
        #     log(f"currentFacts")
        #     currentFacts.dump()
        # log_vars(parentFacts=parentFacts, currentFacts=currentFacts)
        # 5. Iterate all parent nodes
        if includeParentPart:
            parentParts = self.getParentCommandParts(reverse=True)
            commandParts.extend(parentParts)
        # 4. Append cliName of current node to command string parts
        log(f"Processing current node {self.ansibleName}")
        if self.cliName:
            commandParts.append(self.cliName)

        # For FixedParamNode, command value is not applicable,
        # but ensure that facts has value popoulated
        result, value = self.getCommandValue(currentFacts, state)
        if not result:
            commandParts = None
            return commandParts

        # Typically two commands will be present when NEGATE_CMD
        # is not set, so need to choose the right one based on value and state
        if not self.negateCommand:
            # For deleted state, choose the one that does not match with the value
            if state == Constant.STATE_DELETED:
                if value is strToBool(self.ansibleValue):
                    commandParts = None
                    return commandParts
            # For other states, choose the one that match with the value
            else:
                if value is not strToBool(self.ansibleValue):
                    commandParts = None
                    return commandParts

        # 2. For each children
        for key, child in self.children.items():
            log(f"Processing child node {child.cliName}, {child.ansibleName}")
            # Append cliName directly for SkipNode
            if isinstance(child, SkipNode):
                commandParts.append(child.cliName)
            else:
                factsTmp = None
                if isinstance(parentFacts, Facts):
                    factsTmp = parentFacts.find(child.ansibleName)
                elif isinstance(parentFacts, dict):
                    factsTmp = parentFacts.get(child.ansibleName, None)
                else: pass

                if factsTmp:
                    commandPartsTmp = child.generateCommandParts(parentFacts,
                                                                 factsTmp,
                                                                 state)
                    if commandPartsTmp:
                        commandParts.extend(commandPartsTmp)

        # 6. Generate command parts for next node and append
        if self.next:
            log(f"Processing next node {self.next.ansibleName}")
            factsTmp = None
            if isinstance(parentFacts, Facts):
                factsTmp = parentFacts.find(self.next.ansibleName)
            elif isinstance(parentFacts, dict):
                factsTmp = parentFacts.get(self.next.ansibleName, None)
            else: pass

            if factsTmp:
                commandPartsTmp = self.next.generateCommandParts(parentFacts,
                                                                 factsTmp,
                                                                 state)
                # If the next node is mandatory parameter, it will be available
                # in either match, diff or haveOnly of grantParentFacts
                if not commandPartsTmp and not self.next.optional and \
                   grantParentFacts:
                    factsTmp = None
                    if grantParentFacts.diff is not None:
                        factsTmp = grantParentFacts.diff
                    elif grantParentFacts.match is not None:
                        factsTmp = grantParentFacts.match
                    elif grantParentFacts.haveOnly is not None:
                        factsTmp = grantParentFacts.haveOnly

                    if factsTmp:
                        commandPartsTmp = self.next.generateCommandParts(factsTmp,
                                                                     factsTmp,
                                                                     state)
                if commandPartsTmp:
                    commandParts.extend(commandPartsTmp)

        self.addNegateCommand(value, commandParts, state)

        log_vars(commandParts=commandParts)
        return commandParts


    def generateCommandValue(self, commandParts, factsNode, state):
        result = True

        # For FixedParamNode, command value is not applicable,
        # but ensure that facts has value popoulated
        result, value = super().getCommandValue(factsNode, state)

        return result

    # generateMergeCommands not to be overridden
    # generateDeleteAllCommands not to be defined
    # generateDeleteCommands not to be overridden
    # generateReplaceCommands not to be overridden

# InterfaceParameter node
class InterfaceParamNode(ParamNode):

    # Methods
    def __init__(self, parent=None, cliName=None, ansibleName=None,
                 ansibleWord=None):
        super().__init__(parent=parent, cliName=cliName,
                         ansibleName=ansibleName,
                         ansibleWord=ansibleWord)

    # Get ansible value from command line
    def getAnsibleValue(self, line):
        value = None
        lineLeft = None

        if isinstance(line, str):
            # Split by two occurances & concatenate the first two parts
            # to form interface name
            value, lineLeft = splitLine(line, Constant.DELIMITER_CLI_COMMAND_WORD, 2)
        if isinstance(line, enumerate):
            # Extract two tokens & join them to form interface name
            tokenIfType = next(line, None)
            tokenIfId = next(line, None)
            if tokenIfType and tokenIfId:
                value = tokenIfType[1] + tokenIfId[1]
        else:
            log(f"Unknown instance type")

        log_vars(value=value, lineLeft=lineLeft)

        return value, lineLeft

    # Get command value from facts
    def getCommandValue(self, facts, state):
        value = None
        # Call parent method to extract facts value
        result, value = super().getCommandValue(facts, state)
        log_vars(value=value)

        # Split the value as per sonic-cli interface format
        if value:
            valueParts = re.split('(\d+)', value)
            valueParts = list(filter(None, valueParts))
            value = Constant.DELIMITER_CLI_COMMAND_WORD.join(valueParts)
            log_vars(valueParts=valueParts, value=value)

        # 4. Return
        return result, value

# InterfaceKey node
class InterfaceKeyNode(ParamNode):

    # Methods
    def __init__(self, parent=None, ansibleName=None,
                 interfaceName=None):
        super().__init__(parent=parent, ansibleName=ansibleName)
        # Members
        self._interfaceName = interfaceName

    @property
    def interfaceName(self):
        return self._interfaceName

    @interfaceName.setter
    def interfaceName(self, value):
        self._interfaceName = value

    def dump(self):
        """
        @brief Print members of InterfaceKeyNode class
        """
        # log(f"InterfaceKeyNode")
        log_vars(interfaceName=self.interfaceName)
        super().dump()

    # Get ansible value from command line
    def getAnsibleValue(self, line):
        interfaceId = None
        value = None
        lineLeft = None

        if isinstance(line, str):
            # Split by one occurance to extract interface id
            interfaceId, lineLeft = splitLine(line, Constant.DELIMITER_CLI_COMMAND_WORD, 1)

        # Interface name format for vxlan is vtep<vtep-identifier>
        # Shall use the same as ansibleValue
        if self.interfaceName == Constant.IF_NAME_VXLAN and \
           interfaceId.startswith(Constant.VTEP_PREFIX) :
            value = interfaceId
        else:
            value = self.interfaceName + interfaceId

        log_vars(value=value, lineLeft=lineLeft)

        return value, lineLeft

    # Get command value from facts
    def getCommandValue(self, facts, state):
        value = None
        # Call parent method to extract facts value
        result, value = super().getCommandValue(facts, state)

        # Split the value as per sonic-cli interface format
        # and return identifier alone
        if value:
            # Interface name format for vxlan is vtep<vtep-identifier>
            # Shall use the same as ansibleValue
            if self.interfaceName == Constant.IF_NAME_VXLAN and \
               value.startswith(Constant.VTEP_PREFIX):
                value = value
            else:
                valueParts = re.split(self.interfaceName, value)
                value = valueParts[1]

        # 4. Return
        return result, value

# Skip node
class SkipNode(Node):

    # Methods
    def __init__(self, parent=None, cliName=None,
                 ansibleWord=None):
        super().__init__(parent=parent, cliName=cliName,
                         ansibleWord=ansibleWord)
        # Members
        # super().children as next token based commands

    def dump(self):
        """
        @brief Print members of SkipNode class
        """
        # log(f"SkipNode")
        super().dump()

    # buildTree not to be overridden
    # buildCmdsToSearch not to be overridden

    def createFactsNode(self, line, facts):
        """
        @brief For Skip node, facts SHALL not be created, just
               check whether CLI token is matching with cliName
               and return lineLeft

        @param line (str): command line
        @param facts (dict): Parent facts node where new node to be created

        @returns newObj (instance): New object created or parent node
        @returns lineLeft (str): Line left after processing
        """
        newObj = None
        lineLeft = None

        log_vars(line=line, facts=facts)

        # Return when line is empty
        if not line:
            return newObj, lineLeft

        # 1. Split the line with DELIMITER_CLI_COMMAND_WORD by one occurance
        firstPart, lineLeft = splitLine(line, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
        # 2. Check whether firstPart is matching with cliName
        if firstPart != self.cliName:
            # TODO: Throw error
            return newObj, lineLeft
        # 3. Check facts node with matching current node's
        #    ansibleName, if so print error and return
        if self.ansibleName in facts:
            # TODO: Throw error
            return newObj, lineLeft
        # 4. If above is not true, return
        return newObj, lineLeft

    def generateFacts(self, line, facts, listGrpCache=None):
        """
        @brief Generate facts from the config for SkipNode

        @param line (str): Configuration to be converted as facts
        @param facts (dict): Placeholder to update the facts

        @returns None
        """
        # 1. Call createFactsNode, expected to return None as newObj
        newObj, lineLeft = self.createFactsNode(line, facts)
        if newObj:
            # TODO: Unexpected error to be handled
            pass
        # 2. Return when lineLeft is empty
        if not lineLeft:
            return lineLeft
        # 3. Find matching node with next token in children
        child = self.findMatchingChild(lineLeft, facts)
        log_vars(child=child)
        if child:
        # 4. Call generateFacts() with matching child with lineLeft
            lineLeft = child.generateFacts(lineLeft, facts)

        return lineLeft

# List node
class ListNode(Node):

    # Methods
    def __init__(self, parent=None, cliName=None,
                 ansibleWord=None):
        super().__init__(parent=parent, cliName=cliName,
                         ansibleName=ansibleWord.listName,
                         ansibleWord=ansibleWord)
        # Members
        # super().children as list of optional parameter nodes
        # super().next as nested list
        # Remove PARAMETER_INDICATOR from keys
        self._keys = ansibleWord.listKeys.replace(Constant.PARAMETER_INDICATOR, '')
        self._fixedWords = list()
        self._ignoreWordsForDelete = list()
        self._keyNodes = list()

    @property
    def keys(self):
        return self._keys

    @keys.setter
    def keys(self, value):
        # Remove PARAMETER_INDICATOR
        self._keys = value.replace(Constant.PARAMETER_INDICATOR, '')

    @property
    def keyNodes(self):
        return self._keyNodes

    @property
    def fixedWords(self):
        return self._fixedWords

    @property
    def ignoreWordsForDelete(self):
        return self._ignoreWordsForDelete

    def addFixedWordNode(self, obj):
        self._fixedWords.append(obj)

    def addKeyNode(self, obj):
        self._keyNodes.append(obj)

    def addIgnoreWordForDelete(self, obj):
        self._ignoreWordsForDelete.append(obj)

    def dump(self):
        """
        @brief Print members of ListNode class
        """
        # log(f"ListNode")
        log_vars(cliName=self.cliName, ansibleName=self.ansibleName, keys=self.keys)
        log_vars(fixedWords=self.fixedWords)
        log_vars(ignoreWordsForDelete=self.ignoreWordsForDelete)
        log_vars(exitCmd=self.exitCmd)
        if self.keyNodes:
            log(f"Keys of {self.cliName}, {self.ansibleName}")
            for keyNode in self.keyNodes:
                keyNode.dump()
        self.dumpChildren()
        if self.next:
            log(f"Next of {self.cliName}, {self.ansibleName}")
            self.next.dump()

    def updateListPath(self, listCache):
        # 4. Update listPath into listCache
        listPathItems = list()
        # 4.1. Build list path syntax for current node 
        #      from ansibleName and keys and append to listPathItems
        pathTmp = buildListPath(self.ansibleName, self.keys)
        listPathItems.append(pathTmp)
        # 4.2. Traverse all parent nodes to compute full path
        parent = self.parent
        while parent:
            if isinstance(parent, ModeNode) and \
               parent.cmdNode and parent.cmdNode != self and \
               parent.cmdNode.ansibleName:
                parentNode = parent.cmdNode
            else:
                parentNode = parent

            if isinstance(parentNode, ListNode):
                pathTmp = buildListPath(parentNode.ansibleName,
                                        parentNode.keys)
            else:
                pathTmp = parentNode.ansibleName

            if pathTmp:
                listPathItems.append(pathTmp)

            parent = parent.parent
        # 4.4. Reverse the listPathItems
        listPathItems.reverse()
        log_vars(listPathItems=listPathItems)

        # Remove listPath item of parent from listCache
        # Parent will be taken care while processing current node items
        # during expandFacts and compressFacts
        listPathItemsCount = len(listPathItems[:-1])
        log_vars(listPathItemsCount=listPathItemsCount)
        for index in range(listPathItemsCount):
            if listPathItems[index] and isListPathSyntax(listPathItems[index]):
                log_vars(index=index)
                listPathItemsTmp = listPathItems[:index+1]
                log_vars(listPathItemTmp=listPathItems[index])
                log_vars(listPathItemsTmp=listPathItemsTmp)
                if listPathItemsTmp:
                    listPathTmp = Constant.DELIMITER_LIST_PATH.join(listPathItemsTmp)
                    if listPathTmp in listCache:
                        log(f"Removed {listPathTmp} due to nested list entry {self.ansibleName}")
                        listCache.remove(listPathTmp)

        # 4.5. Compute listPath from listPathItems & DELIMITER_LIST_PATH
        listPath = Constant.DELIMITER_LIST_PATH.join(listPathItems)
        # 4.6. Update listPath into listCache, if not present
        if listPath not in listCache:
            listCache.append(listPath)

    # Create key node
    def createKeyNode(self, line):
        newObj, lineLeft = self.createTreeNode(line)
        return newObj, lineLeft

    # Build tree for keys
    def buildTreeForFixedWords(self, line, skip=False):
        lineLeft = line

        # Skip processing fixed words when cliName is None
        # Sometimes nested list will not have cliName
        if not self.cliName:
            return lineLeft

        # 1. Process all fixedKeywords
        while not isParamNode(lineLeft):
            secondPart = None
            firstPart, lineLeft = splitLine(lineLeft, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
            # Continue if skip flag is set (ListGroup case)
            if skip: continue

            # Check for special flags for fixed keyword handling
            if Constant.INDICATOR_ANSIBLE_WORD in firstPart:
                partsTmp = firstPart.split(Constant.INDICATOR_ANSIBLE_WORD)
                firstPart = partsTmp[0]
                secondPart = partsTmp[1]

            # Add to fixedWords list
            self.addFixedWordNode(firstPart)

            # Add to ignoreWordsForDelete list
            if secondPart and secondPart == Constant.IGN_WORD_FOR_DEL_INDICATOR:
                self.addIgnoreWordForDelete(firstPart)

        return lineLeft

    # Build tree for keys
    def buildTreeForKeys(self, line, skip=False):
        lineLeft = line
        keysCount = len(self.keys.split(Constant.DELIMITER_LIST_KEYS))
        availableKeys = len(self.keyNodes)
        keyIndex = 0

        log_vars(keysCount=keysCount, availableKey=availableKeys)
        # Skip if keys are extracted already
        if keysCount == availableKeys:
            return lineLeft

        # Start building key nodes
        while keyIndex < (keysCount - availableKeys):
            # Create tree node
            newObj, lineLeft = self.createKeyNode(lineLeft)
            if not skip:
                self.addKeyNode(newObj)
                log(f"Added {newObj.cliName}, {newObj.ansibleName} in keyNodes")
            keyIndex = keyIndex + 1

        return lineLeft

    # Check whether a node is key node or not
    def isKeyNode(self, node):
        result = False

        if not node: return result

        keys = self.keys.split(Constant.DELIMITER_LIST_KEYS)

        if not keys:
            return result

        if node.ansibleName in keys:
            result = True

        return result

    # Find the node based on ansibleName
    def findNode(self, ansibleName):
        result = None

        if not ansibleName: return result

        # Search in keyNodes
        for node in self.keyNodes:
            if node.ansibleName == ansibleName:
                result = node
                break

        if result: return result

        # Search in children
        for key, node in self.children.items():
            if node.ansibleName == ansibleName:
                result = node
                break

        log_vars(result=result)
        return result

    # Build tree for children
    def buildTreeForChildren(self, line, listCache):
        lineLeft = line

        # Return when line is empty
        if not lineLeft:
            return lineLeft

        # Create tree node
        newObj, lineLeft = self.createTreeNode(lineLeft)

        # Nested list case
        if isinstance(newObj, ListNode):
            self.next = newObj
            lineLeft = newObj.buildTree(lineLeft, listCache)
        elif self.isKeyNode(newObj):
            self.addKeyNode(newObj)
            log(f"Added {newObj.cliName}, {newObj.ansibleName} in keyNodes")
            lineLeft = self.buildTreeForChildren(lineLeft, listCache)
        else:
            while newObj:
                # If parent name is mentioned, add the newObj into respective parent node
                if newObj.parentName:
                    parentNode = self.findNode(newObj.parentName)
                    if parentNode:
                        newObj.parent = parentNode
                        parentNode.addChild(newObj.cliName, newObj)
                        log(f"Added {newObj.cliName}, {newObj.ansibleName} in children of {parentNode.cliName}, {parentNode.ansibleName}")
                    else:
                        log(f"Parent for {newObj.cliName}, {newObj.ansibleName} in not found")
                else:
                    self.addChild(newObj.cliName, newObj)
                    log(f"Added {newObj.cliName}, {newObj.ansibleName} in children")
                # If newObj is not optional parameter or not based on parent value,
                # continue buildTree for newObj
                if not newObj.optional and not newObj.ifParentValue:
                    lineLeft = newObj.buildTree(lineLeft, listCache)
                # Create tree node
                newObj, lineLeft = self.createTreeNode(lineLeft)

        return lineLeft

    def buildTree(self, line, listCache):
        """
        @brief Build tree for command based on list for ListNode class

        @param line (str): Command syntax
        @param listCache (dict): Placeholder to update all list nodes
                                 required for compress & expand facts

        @returns None
        """
        # Format of command
        # command: word [more words] [$positional_key] [more positional keys] [param-word $ansibleName] [more params]
        # All tokens without $ from start of command are treated as keywords
        # Tokens with $ prefix after all keywords are treated as positional keys
        # Tokens with word & next token with $ are treated as param name & param value
        # Parameter value token shall contain ansible argspec name
        lineLeft = line

        # Return when line is empty
        if not line:
            return

        # 4. Update listPath into listCache
        self.updateListPath(listCache)

        # If line starts with parameter, call createTreeNode
        # If line does not start with parameter, extract all fixed words
        lineLeft = self.buildTreeForFixedWords(line)

        lineLeft = self.buildTreeForKeys(lineLeft)

        if lineLeft:
            self.buildTreeForChildren(lineLeft, listCache)

    def buildCmdsToSearch(self, commands):
        """
        @brief Build commands to search for while generating facts
               for ListNode class

        @param commands (list): Placeholder to update the command

        @returns None
        """
        # 1. Form temp list
        commandParts = list()
        # 2. Traverse back with parent node and append to temp list
        parentParts = self.getParentCommandParts(reverse=True)
        commandParts.extend(parentParts)
        # 4. Append cliName of current node to temp list
        commandParts.append(self.cliName)
        # 5. Iterate fixedWords
        for word in self.fixedWords:
        # 6. Append cliName of each item into temp list
            commandParts.append(word)
        # 7. Join all items of temp list with SPACE
        command = convertToCommand(commandParts)
        # 8. Append formed cmdPattern to commands argument
        commands.append(command)
        # For ListGroup, few commands appear with 'no ' in
        # show running-config, hence add 'no' into cmdsToSearch list
        if isinstance(self, ListGroupNode):
            commandParts.insert(0, Constant.CLI_COMMAND_NO_KEYWORD_TOKEN)
            # 9. Join all items of temp list with SPACE
            command = convertToCommand(commandParts)
            # 10. Append formed cmdPattern to commands argument
            commands.append(command)

    def createFactsNode(self, line, facts):
        """
        @brief Create facts node (if not present) instance from line
               for ListNode class

        @param line (str): command line
        @param facts (dict): Parent facts node where new node to be created

        @returns newObj (instance): New object created or parent node
        @returns lineLeft (str): Line left after processing
        """
        newObj = None
        lineLeft = None

        log_vars(line=line, facts=facts)

        # Return when line is empty
        if not line:
            return newObj, lineLeft

        lineLeft = line
        if self.cliName:
            # 1. Split the line with DELIMITER_CLI_COMMAND_WORD by one occurance
            firstPart, lineLeft = splitLine(lineLeft, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
            # 2. Check whether firstPart is matching with cliName
            if firstPart != self.cliName:
                # TODO: Throw error
                log(f"{firstPart} is not matching with {self.cliName}")
                return newObj, lineLeft
        # 3. Check facts node with matching current node's
        #    ansibleName, if so print error and return
        if self.ansibleName in facts:
            # If facts node is present, return parent node
            newObj = facts
            return newObj, lineLeft
        # 4. If above is not true, create facts node with current node's
        #    ansibleName as key & list as value
        newObj = {self.ansibleName: list()}
        # 5. Add new node into facts
        facts.update(newObj)
        # 6. Return new node and lineLeft
        return newObj, lineLeft

    def generateFactsForChildren(self, line, facts):
        if not line or not facts:
            return

        log_vars(line=line)

        lineLeft = line

        for key, child in self.children.items():
            log(f"Checking against {key}, {child.cliName}, {child.ansibleName}")
            # Break when lineLeft is empty
            if not lineLeft: break
            if child.optional:
                if child.cliName:
                    found = False
                    # Check whether cliName is present in line first
                    if lineLeft.startswith(child.cliName + Constant.DELIMITER_CLI_COMMAND_WORD) or \
                       lineLeft == child.cliName:
                        found = True
                    # Check whether ifNextValue is present and satisfied
                    if found and child.ifNextValue:
                        if child.validateNextValue(line):
                            found = True
                        else:
                            found = False
                    if found:
                        lineLeft = child.generateFacts(lineLeft, facts)
                else:
                    lineLeft = child.generateFacts(lineLeft, facts)
            else:
                lineLeft = child.generateFacts(lineLeft, facts)

        log_vars(lineLeft=lineLeft)

        return lineLeft

    def generateFactsForFixedWords(self, line, facts):
        if not line:
            return

        log_vars(line=line)

        lineLeft = line
        # 4. For each fixedWords, skip those many tokens from lineIt
        #    In general, fixedNode will not have respective ansible node
        for word in self.fixedWords:
            token, lineLeft = splitLine(lineLeft, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
            if not token:
                # TODO: Throw error
                log(f"Iterator is empty")
                break

        log_vars(lineLeft=lineLeft)

        return lineLeft

    def generateFactsForKeys(self, line, facts):
        if not line:
            return

        log_vars(line=line)

        lineLeft = line
        # 5. For each positional keys, extract ansible value from lineIt
        #    create new facts node and add to currFactsNode
        for keyNode in self.keyNodes:
            lineLeft = keyNode.generateFacts(lineLeft, facts)
            if not lineLeft:
                log(f"Iterator is empty")
                break

        log_vars(lineLeft=lineLeft)

        return lineLeft

    def generateFacts(self, line, facts, listGrpCache=None):
        """
        @brief Generate facts from the config for ListNode class

        @param config (NetworkConfig): Configurations to be converted as facts
        @param facts (dict): Placeholder to update the facts

        @returns currFactsNode (dict) : Newly created facts node for list entry
        """
        listFactsNode = None
        # 1. Create facts node for list, if not present
        listFactsNode, lineLeft = self.createFactsNode(line, facts)
        listFactsNodeVal = listFactsNode.get(self.ansibleName, None)
        # 3. Create temp list entry node
        currFactsNode = dict()
        # 2. Start generating facts for current list entry
        # Generate facts for fixed words
        lineLeft = self.generateFactsForFixedWords(lineLeft, None)
        # Generate facts for keys
        lineLeft = self.generateFactsForKeys(lineLeft, currFactsNode)

        # Generate facts for nested list
        if self.next:
            log(f"Generate facts for nested list")
            log_vars(lineLeft=lineLeft, currFactsNode=currFactsNode)

            listEntryKeyParts = list()
            # Locate the outer list entry, if processed already
            for keyNode in self.keyNodes:
                keyVal = currFactsNode.get(keyNode.ansibleName)
                if keyVal:
                    listEntryKeyParts.append(keyVal)
            log_vars(listEntryKeyParts=listEntryKeyParts)

            # Generate listEntry key
            listEntryKey = Constant.DELIMITER_LIST_KEYS.join(listEntryKeyParts)
            log_vars(listEntryKey=listEntryKey)
            # Locate the list entry node, if present, generate
            # facts for inner list entry
            listEntryNode = listGrpCache.get(listEntryKey, None)
            log_vars(listEntryNode=listEntryNode)
            if listEntryNode:
                currFactsNode = listEntryNode
            # 7. Add temp entry node into list node
            else:
                listGrpCache.update({listEntryKey: currFactsNode})
                # Add temp entry node into list node
                listFactsNodeVal.append(currFactsNode)

            self.next.generateFacts(lineLeft, currFactsNode, listGrpCache)
            log_vars(listFactsNodeVal=listFactsNodeVal)
            return currFactsNode
        # 6. Rest of the line parts will be parameters,
        #    call generateFactsForChildren
        self.generateFactsForChildren(lineLeft, currFactsNode)
        # 7. Add temp entry node into list node
        listFactsNodeVal.append(currFactsNode)
        log_vars(listFactsNodeVal=listFactsNodeVal)

        return currFactsNode

    def generateCommandsForNextNodeInternal(self, parentFacts,
                                    currentFacts, parentCommandParts,
                                    state):
        commands = list()
        grandParentFacts = None

        for key, item in currentFacts.items():
            log(f"Processing {key}, {item}")
            commandParts = list()
            commandParts.extend(parentCommandParts)
            partsTmp = self.generateCommonCommandParts(item, key, state)
            commandParts.extend(partsTmp)

            # Skip adding children for deleted state
            # In general, adding children for delete is not required,
            # but prefix-list command expects the children to be present.
            # TODO: Enable this once prefix-list delete is fixed
            if state != Constant.STATE_DELETED:
                grandParentFacts = parentFacts.find(key)
            partsTmp = self.generateCommandForChildren(grandParentFacts,
                                                       currentFacts, item,
                                                       state)
            log_vars(partsTmp=partsTmp)
            if partsTmp:
                commandParts.extend(partsTmp)

            # 7. Form command string with joining all parts with SPACE
            command = convertToCommand(commandParts)
            commands.append(command)

        log_vars(commands=commands)
        return commands


    # Generate command parts for nested list
    def generateCommandsForNextNode(self, parentFacts,
                                    currentFacts, parentCommandParts,
                                    state):
        commands = list()

        # Deleted handling
        if state == Constant.STATE_DELETED:
            if currentFacts:
                log(f"Processing match nodes")
                commandsTmp = self.generateCommandsForNextNodeInternal(parentFacts,
                                                         currentFacts,
                                                         parentCommandParts,
                                                         state)
                if commandsTmp:
                    commands.extend(commandsTmp)
                    log_vars(commands=commands)

            return commands

        # Merge, Replace & Overridden handling
        # Process wantOnly nodes
        if currentFacts and currentFacts.wantOnly:
            log(f"Processing wantOnly nodes")
            commandsTmp = self.generateCommandsForNextNodeInternal(parentFacts,
                                                     currentFacts.wantOnly,
                                                     parentCommandParts,
                                                     state)
            if commandsTmp:
                commands.extend(commandsTmp)

        # Process diff nodes
        if currentFacts and currentFacts.diff:
            log(f"Processing diff nodes")
            commandsTmp = self.generateCommandsForNextNodeInternal(parentFacts,
                                                     currentFacts.diff,
                                                     parentCommandParts,
                                                     state)
            if commandsTmp:
                commands.extend(commandsTmp)

        return commands

    def generateKeyParts(self, parentFacts, currentFacts, state):
        commandParts = list()
        # 6. For each keyNode item,
        for keyNode in self.keyNodes:
            commandPartsTmp = keyNode.generateCommandParts(currentFacts,
                                                         currentFacts,
                                                         state)
            if commandPartsTmp:
                commandParts.extend(commandPartsTmp)

        log_vars(commandParts=commandParts)
        return commandParts

    def generateCommonCommandParts(self, facts, key, state):
        commandParts = list()
        if self.cliName:
            commandParts.append(self.cliName)
        # 4. If fixedWords is present,
        for word in self.fixedWords:
        #    4.1 apppend all fixed keywords to temp command string parts
            # Check whether word is present in ignoreWordsForDelete list or not
            if self.ignoreWordsForDelete:
                if state == Constant.STATE_DELETED and \
                   word in self.ignoreWordsForDelete:
                    log(f"Fixed word {word} is ignored for delete command")
                else:
                    commandParts.append(word)
            else:
                commandParts.append(word)
        # Append keys
        if key:
            keyParts = self.generateKeyParts(facts, facts, state)
            commandParts.extend(keyParts)

        return commandParts

    def generateModeCommand(self, facts, key):
        command = None
        commandParts = list()

        # log_vars(key=key, facts=facts)
        parentParts = self.getParentCommandParts(reverse=True)
        commandParts.extend(parentParts)
        commonParts = self.generateCommonCommandParts(facts, key, Constant.STATE_MERGED)
        commandParts.extend(commonParts)

        if commandParts:
            command = convertToCommand(commandParts)

        return command

    def generateModeDeleteCommand(self, facts, key):
        command = None
        commandParts = list()

        log_vars(key=key)

        parentParts = self.getParentCommandParts(reverse=True)
        commandParts.extend(parentParts)
        commonParts = self.generateCommonCommandParts(facts, key, Constant.STATE_DELETED)
        commandParts.extend(commonParts)
        negateCommand(commandParts)

        if commandParts:
            command = convertToCommand(commandParts)

        return command

    def generateCommandForChildren(self, grantParentFacts,
                                   parentFacts, currentFacts, state):
        commandParts = list()
        # 6. For each children in item,
        for key, child in self.children.items():
            commandPartsTmp = child.generateCommandParts(currentFacts,
                                                         currentFacts,
                                                         state,
                                                         grantParentFacts=grantParentFacts)

            # If the child is mandatory parameter, it will be available
            # in match list of grantParentFacts
            if not commandPartsTmp and not child.optional:
                log(f"Attempting to generateCommand from grantParentFacts for {child.ansibleName}")
                factsTmp = None
                if grantParentFacts.match is not None:
                    factsTmp = grantParentFacts.match.get(child.ansibleName, None)
                if not factsTmp and grantParentFacts.haveOnly is not None:
                    factsTmp = grantParentFacts.haveOnly.get(child.ansibleName, None)

                if factsTmp:
                    commandPartsTmp = child.generateCommandParts(parentFacts,
                                                                 factsTmp,
                                                                 state,
                                                                 grantParentFacts=grantParentFacts)

            if commandPartsTmp:
                commandParts.extend(commandPartsTmp)

        log_vars(commandParts=commandParts)
        return commandParts

    def generateMergeCommandsInternal(self, parentFacts, currentFacts,
                                      includeDiff=False, includeMatch=False,
                                      includeHaveOnly=False):
        commands = list()

        parentCommandParts = self.getParentCommandParts(reverse=True)

        log_vars(currentFacts=currentFacts)
        for key, item in currentFacts.items():
            log(f"Processing {key}")
            diffNode = None
            matchNode = None
            haveOnlyNode = None
            # Create temp command string parts
            commandParts = list()
            commandParts.extend(parentCommandParts)
            commonParts = self.generateCommonCommandParts(item, key, Constant.STATE_MERGED)
            commandParts.extend(commonParts)

            grandParentFacts = parentFacts.find(key)
            # Generate command for next node
            if self.next:
                log(f"Processing next list {self.next.ansibleName}")
                currentFactsTmp = parentFacts.find(key)
                if not currentFactsTmp:
                    continue

                nextListFacts = currentFactsTmp.find(self.next.ansibleName)
                if not nextListFacts:
                    continue

                #log("currentFactsTmp")
                #currentFactsTmp.dump()
                #log("nextListFacts")
                #nextListFacts.dump()

                # nextListFacts.dump()
                commandsTmp = self.next.generateCommandsForNextNode(nextListFacts,
                                                              nextListFacts,
                                                              commandParts,
                                                              Constant.STATE_MERGED)
                if commandsTmp:
                    commands.extend(commandsTmp)
                    continue

            # Generate command parts for children and append
            childCommandParts = self.generateCommandForChildren(grandParentFacts,
                                                                currentFacts,
                                                                item,
                                                                Constant.STATE_MERGED)
            commandParts.extend(childCommandParts)
            # Get diff node matching the key of current item
            if includeDiff and parentFacts.diff:
                diffNode = parentFacts.diff.pop(key, None)
            if diffNode:
                childCommandParts = self.generateCommandForChildren(grandParentFacts,
                                                                    currentFacts, diffNode,
                                                                    Constant.STATE_MERGED)
                commandParts.extend(childCommandParts)
            # Get match node matching the key of current item
            if includeMatch and parentFacts.match:
                matchNode = parentFacts.match.pop(key, None)
            if matchNode:
                childCommandParts = self.generateCommandForChildren(grandParentFacts,
                                                                    currentFacts, matchNode,
                                                                    Constant.STATE_MERGED)
                commandParts.extend(childCommandParts)
            # Get haveOnly node matching the key of current item
            if includeHaveOnly and parentFacts.haveOnly:
                haveOnlyNode = parentFacts.haveOnly.pop(key, None)
            if haveOnlyNode:
                childCommandParts = self.generateCommandForChildren(grandParentFacts,
                                                                    currentFacts, haveOnlyNode,
                                                                    Constant.STATE_MERGED)
                commandParts.extend(childCommandParts)

            # 7. Form command string with joining all parts with SPACE
            command = convertToCommand(commandParts)
            commands.append(command)
            log_vars(command=command)

        return commands


    def generateMergeCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : merged)
               for ListNode class

        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config
        @param config (NetworkConfig): Placeholder to append config

        @returns None
        """
        # parentFacts.dump()
        # currentFacts.dump()
        # Main metod starts here
        commands = list()
        # 1. Iterate all keys in want-only facts, for each item
        if currentFacts and currentFacts.wantOnly:
            log(f"Processing wantOnly nodes")
            commandsTmp = self.generateMergeCommandsInternal(currentFacts,
                                                             currentFacts.wantOnly,
                                                             includeDiff=True)
            commands.extend(commandsTmp)

        # 1. Iterate all keys in diff facts, for each item
        if currentFacts.diff:
            log(f"Processing diff nodes")
            commandsTmp = self.generateMergeCommandsInternal(currentFacts,
                                                             currentFacts.diff)
            commands.extend(commandsTmp)

        log_vars(commands=commands)
        # 8. Create ConfigLine instance with command string and add to config
        addToConfig(config, commands, parentCommand)
        # 3. Call generateMergeSingleEntry with item
        # 5. Append generated command into tmp list
        # 6. Iterate all keys in diff, for each item
        # 8. Call generateMergeSingleEntry with item
        # 9. Append generated command into tmp list
        # 10. Add command list into config with parentCommand

    def ignoreMatchOnlyNodes(self, facts):
        toBeRemoved = list()

        if not facts or not facts.match:
            return

        for key, item in facts.match.items():
            if (facts.diff is None or (facts.diff is not None and not key in facts.diff)) and \
               (facts.wantOnly is None or (facts.wantOnly is not None and not key in facts.wantOnly)) and \
               (facts.haveOnly is None or (facts.haveOnly is not None and not key in facts.haveOnly)):
                toBeRemoved.append(key)

        log_vars(toBeRemoved=toBeRemoved)
        for key in toBeRemoved:
            facts.match.pop(key)

        return

    def generateDeleteCommandsInternal(self, facts, parentCommand,
                                       config, removedKeys=None):
        log_vars(removedKeys=removedKeys)
        # 1. Create temp command string parts
        commandParts = list()
        parentCommandParts = self.getParentCommandParts(reverse=True)
        # 2. Get all parent nodes' cliName & append to command string parts
        # 3. Reverse temp command string parts
        # 4. Insert "no" keyword at begining to temp command string parts
        if facts:
            for key, item in facts.items():
                log(f"Processing {key}")
                if removedKeys and key in removedKeys:
                    continue
            # Create temp command string parts
                commandParts = list()
                commandParts.extend(parentCommandParts)
                commonParts = self.generateCommonCommandParts(item, key, Constant.STATE_DELETED)
                commandParts.extend(commonParts)
                negateCommand(commandParts)

                # Generate command for next node
                if self.next:
                    log(f"Processing next list {self.next.ansibleName}")
                    nextListItems = item.get(self.next.ansibleName, None)
                    if not nextListItems:
                        continue

                    log_vars(nextListItems=nextListItems)
                    commandsTmp = self.next.generateCommandsForNextNode(nextListItems,
                                                                        nextListItems,
                                                                        commandParts,
                                                                        Constant.STATE_DELETED)
                    if commandsTmp:
                        log_vars(commandsTmp=commandsTmp)
                        addToConfig(config, commandsTmp, parentCommand)
                        continue

            # 7. Form command string with joining all parts with SPACE
                command = convertToCommand(commandParts)
                log_vars(command=command)
                addToConfig(config, command, parentCommand)
                if removedKeys:
                    removedKeys.append(key)

    def generateDeleteCommands(self, parentFacts, currentFacts,
                              parentCommand, config, removedKeys=None):
        """
        @brief Generate config from the facts (state : deleted)
               for ListNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        """
        # 5. If fixedWords is present,
        #    5.1 apppend all fixed keywords to temp command string parts
        # 6. For each positional keys,
        #    6.1 Locate respective facts node
        #    6.2 Fetch ansibleValue & append to temp command string parts
        # 7. Form command string with joining all parts with SPACE
        # 8. Create ConfigLine instance with command string and add to config
        self.generateDeleteCommandsInternal(currentFacts.match, parentCommand,
                                            config, removedKeys=removedKeys)
        self.generateDeleteCommandsInternal(currentFacts.diff, parentCommand,
                                            config, removedKeys=removedKeys)

    def generateDeleteAllCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : deleted)
               for ListNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        """
        removedKeys = list()
        # Generate delete for match nodes
        self.generateDeleteCommandsInternal(currentFacts.match, parentCommand,
                                            config, removedKeys=removedKeys)
        # Generate delete for diff nodes
        self.generateDeleteCommandsInternal(currentFacts.diff, parentCommand,
                                            config, removedKeys=removedKeys)
        # Generate delete for haveOnly nodes
        self.generateDeleteCommandsInternal(currentFacts.haveOnly, parentCommand,
                                            config, removedKeys=removedKeys)

    def generateReplaceCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : deleted)
               for ListNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        """
        removedKeys = list()

        # Ignore nodes that are present in match only
        self.ignoreMatchOnlyNodes(currentFacts)

        # Generate delete for match nodes
        self.generateDeleteCommandsInternal(currentFacts.match, parentCommand,
                                            config, removedKeys=removedKeys)
        # Generate delete for diff nodes
        self.generateDeleteCommandsInternal(currentFacts.diff, parentCommand,
                                            config, removedKeys=removedKeys)
        # Generate merge for want-only, diff & match nodes
        commands = list()
        parentCommandParts = self.getParentCommandParts(reverse=True)
        # 1. Iterate all keys in want-only facts, for each item
        if currentFacts.wantOnly:
            log(f"Processing wantOnly nodes")
            commandsTmp = self.generateMergeCommandsInternal(currentFacts,
                                                             currentFacts.wantOnly,
                                                             includeDiff=True,
                                                             includeMatch=True)
            commands.extend(commandsTmp)

        # 1. Iterate all keys in diff facts, for each item
        if currentFacts.diff:
            log(f"Processing diff nodes")
            commandsTmp = self.generateMergeCommandsInternal(currentFacts,
                                                             currentFacts.diff,
                                                             includeMatch=True)
            commands.extend(commandsTmp)

        # 8. Create ConfigLine instance with command string and add to config
        addToConfig(config, commands, parentCommand)

    def generateOverriddenCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : overridden)
               for ListNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        """
        # currentFacts.dump()

        # Ignore nodes that are present in match only
        self.ignoreMatchOnlyNodes(currentFacts)

        # Generate delete for match, diff & haveOnly nodes
        self.generateDeleteAllCommands(parentFacts, currentFacts,
                                       parentCommand, config)
        # Generate merge for want-only, diff & match nodes
        commands = list()
        parentCommandParts = self.getParentCommandParts(reverse=True)
        # 1. Iterate all keys in want-only facts, for each item
        if currentFacts.wantOnly:
            log(f"Processing wantOnly nodes")
            commandsTmp = self.generateMergeCommandsInternal(currentFacts,
                                                             currentFacts.wantOnly,
                                                             includeDiff=True,
                                                             includeMatch=True,
                                                             includeHaveOnly=True)
            commands.extend(commandsTmp)

        # 1. Iterate all keys in diff facts, for each item
        if currentFacts.diff:
            log(f"Processing diff nodes")
            commandsTmp = self.generateMergeCommandsInternal(currentFacts,
                                                             currentFacts.diff,
                                                             includeMatch=True,
                                                             includeHaveOnly=True)
            commands.extend(commandsTmp)

        # 1. Iterate all keys in match facts, for each item
        if currentFacts.match:
            log(f"Processing match nodes")
            commandsTmp = self.generateMergeCommandsInternal(currentFacts,
                                                             currentFacts.match,
                                                             includeHaveOnly=True)
            commands.extend(commandsTmp)

        # 8. Create ConfigLine instance with command string and add to config
        addToConfig(config, commands, parentCommand)

# InterfaceList node
class InterfaceListNode(ListNode):

    # Methods
    def __init__(self, parent=None, cliName=None,
                 ansibleWord=None):
        super().__init__(parent=parent, cliName=cliName,
                         ansibleWord=ansibleWord)
        # Members
        self._interfaceName = None

    @property
    def interfaceName(self):
        return self._interfaceName

    @interfaceName.setter
    def interfaceName(self, value):
        self._interfaceName = value

    def dump(self):
        """
        @brief Print members of InterfaceListNode class
        """
        # log(f"InterfaceListNode")
        log_vars(negateCommand=self.negateCommand)
        log_vars(interfaceName=self.interfaceName)
        super().dump()

    def createKeyNode(self, line):
        # Extract ansibleName
        ansibleName, lineLeft = splitLine(line, Constant.DELIMITER_CLI_COMMAND_WORD, 1)

        ansibleName = getParamName(ansibleName)
        # Interface name is saved in fixed word
        self.interfaceName = self.fixedWords[0]
        newObj = InterfaceKeyNode(parent=self,
                                  ansibleName=ansibleName,
                                  interfaceName=self.interfaceName)

        return newObj, lineLeft

    def generateKeyParts(self, parentFacts, currentFacts, state):
        keyParts = list()

        # Generate keyParts from parent class method
        keyPartsTmp = super().generateKeyParts(parentFacts, currentFacts, state)

        if not keyPartsTmp:
            return keyParts

        # For vxlan interface, interface name pattern is
        # vtep<vtep-identifer>, so treat interface name as it is
        if self.interfaceName == Constant.IF_NAME_VXLAN:
            keyParts = keyPartsTmp
        # Strip out interface name for type other than VXLAN
        else:
            for keyPartTmp in keyPartsTmp:
                keyPartTmp = keyPartTmp.replace(self.interfaceName, '')
                keyParts.append(keyPartTmp)

        # log_vars(keyParts=keyParts)
        return keyParts

    def isValidInterfaceName(self, key):
        result = False
        interfaceName = None

        # Return when key is empty or None
        if not key: return result

        keyParts = key.split(Constant.DELIMITER_LIST_KEY_PAIR)
        keyVal = keyParts[1]

        # Check whether key contains interfaceName
        # For vxlan, interface name shall be vtep<vtep-identifier>
        # so check against VTEP_PREFIX
        if self.interfaceName == Constant.IF_NAME_VXLAN:
            ifNamePrefix = Constant.VTEP_PREFIX
        else:
            ifNamePrefix = self.interfaceName

        if ifNamePrefix and keyVal.startswith(ifNamePrefix):
            result = True

        return result

    def generateModeCommand(self, facts, key):
        command = None

        if not self.isValidInterfaceName(key):
            return command

        # Invoke parent method
        command = super().generateModeCommand(facts, key)

        return command

    def generateModeDeleteCommand(self, facts, key):
        command = None

        # Return if delete command is not allowed
        if not self.negateCommand:
            return command

        # Return if interface name is not matching with key
        if not self.isValidInterfaceName(key):
            return command

        # Invoke parent method
        command = super().generateModeDeleteCommand(facts, key)

        return command

# ListGroup node
class ListGroupNode(ListNode):

    # Methods
    def __init__(self, parent=None, cliName=None,
                 ansibleWord=None):
        super().__init__(parent=parent, cliName=cliName,
                         ansibleWord=ansibleWord)

    # Build tree for keys
    def buildTreeForKeys(self, line, skip=False):
        lineLeft = line
        keysCount = len(self.keys.split(Constant.DELIMITER_LIST_KEYS))
        keyIndex = 0

        # Start building key nodes, but skip adding to keyNodes list
        while keyIndex < keysCount:
            # Create tree node
            newObj, lineLeft = self.createKeyNode(lineLeft)
            if not skip:
                self.addKeyNode(newObj)
                log(f"Added {newObj.cliName}, {newObj.ansibleName} in keyNodes")
            keyIndex = keyIndex + 1

        return lineLeft

    # Build tree for children
    def buildTreeForChildren(self, line, listCache):
        lineLeft = line

        # Return when line is empty
        if not lineLeft:
            return lineLeft

        # Create tree node
        newObj, lineLeft = self.createTreeNode(lineLeft)

        # Nested list case
        if isinstance(newObj, ListNode):
            self.next = newObj
            lineLeft = newObj.buildTree(lineLeft, listCache)
        elif self.isKeyNode(newObj):
            self.addKeyNode(newObj)
            log(f"Added {newObj.cliName}, {newObj.ansibleName} in keyNodes")
            lineLeft = self.buildTreeForChildren(lineLeft, listCache)
        else:
            while newObj:
                key = newObj.buildKey()
                # If parent name is mentioned, add the newObj into respective parent node
                log_vars(key=key, cliName=newObj.cliName, ansibleName=newObj.ansibleName, parentName=newObj.parentName)
                if newObj.parentName:
                    parentNode = self.findNode(newObj.parentName)
                    if parentNode:
                        newObj.parent = parentNode
                        parentNode.addChild(key, newObj)
                        log(f"Added {newObj.cliName}, {newObj.ansibleName} in children of {parentNode.cliName}, {parentNode.ansibleName}")
                    else:
                        log(f"Parent for {newObj.cliName}, {newObj.ansibleName} in not found")
                else:
                    currObj = self.addChild(key, newObj)
                    if currObj:
                        newObj = currObj
                    log(f"Added {newObj.cliName}, {newObj.ansibleName} in children")
                # If newObj is not optional parameter or not based on parent value,
                # continue buildTree for newObj
                if not newObj.optional and not newObj.ifParentValue:
                    lineLeft = newObj.buildTree(lineLeft, listCache)
                # Create tree node
                newObj, lineLeft = self.createTreeNode(lineLeft)

        return lineLeft

    # Build tree
    def buildTree(self, line, listCache):
        """
        @brief Build tree for command based on list for ListGroupNode class

        @param line (str): Command syntax
        @param listCache (dict): Placeholder to update all list nodes
                                 required for compress & expand facts

        @returns None
        """
        # Return when line is empty
        if not line:
            return

        # If called for the first time, invoke parent method
        if not self.keyNodes:
            super().buildTree(line, listCache)
            log_vars(listCache=listCache)
            return

        # Call parent method, but skip adding into the tree
        lineLeft = super().buildTreeForFixedWords(line, skip=True)

        # Call parent method, but skip adding into the tree
        lineLeft = self.buildTreeForKeys(lineLeft, skip=True)

        # Call parent method & add the current child
        if lineLeft:
            self.buildTreeForChildren(lineLeft, listCache)

    def generateFactsForChildren(self, line, facts, negateFlag=False):
        if not line or not facts:
            return

        log_vars(line=line)

        lineLeft = line

        for key, child in self.children.items():
            log(f"Checking against {child.cliName}, {child.ansibleName}")
            negateFactsValue = False
            # Break when lineLeft is empty
            if not lineLeft: break
            if child.optional or isinstance(child, Node):
                if child.cliName:
                    found = False
                    # Check whether cliName is present in line first
                    if lineLeft.startswith(child.cliName + Constant.DELIMITER_CLI_COMMAND_WORD) or \
                         lineLeft == child.cliName:
                        found = True
                    # Check whether ifNextValue is present and satisfied
                    if found and child.ifNextValue:
                        if child.validateNextValue(line):
                            found = True
                        else:
                            found = False
                    if found:
                        lineLeft = child.generateFacts(lineLeft, facts)
                else:
                    lineLeft = child.generateFacts(lineLeft, facts)
            else:
                lineLeft = child.generateFacts(lineLeft, facts)
            # Negate the facts value for FixedParamNode, this is required to
            # handle 'no ' commands in ListGroup children
            if negateFlag and isinstance(child, FixedParamNode):
                factsValue = facts.get(child.ansibleName, None)
                if factsValue is not None:
                    factsValue = not factsValue
                    facts.update({child.ansibleName: factsValue})
                    log(f"Negated the facts value for {child.cliName}, {child.ansibleName}")

        log_vars(lineLeft=lineLeft)

        return lineLeft

    def generateFacts(self, config, facts, listGrpCache=None):
        """
        @brief Generate facts from the config for ListGroupNode class

        @param config (NetworkConfig): Configurations to be converted as facts
        @param facts (dict): Placeholder to update the facts

        @returns currFactsNode (dict) : Newly created facts node for list entry
        """
        listFactsNode = None
        listGrpEntryKeyParts = list()
        negateFlag = False

        # Remove 'no ' keyword from config and set negateFlag as True
        if config.startswith(Constant.CLI_COMMAND_NO_KEYWORD_TOKEN + \
                             Constant.DELIMITER_CLI_COMMAND_WORD):
            _, config = splitLine(config, Constant.DELIMITER_CLI_COMMAND_WORD, 1)
            negateFlag = True

        # 1. Create facts node for list, if not present
        listFactsNode, lineLeft = self.createFactsNode(config, facts)
        listFactsNodeVal = listFactsNode.get(self.ansibleName, None)

        listGrpEntryKeyParts.append(self.ansibleName)

        log_vars(listGrpCache=listGrpCache)
        # 2. Start generating facts for current list entry
        # 3. Create temp list entry node
        currFactsNode = dict()
        # Generate facts for fixed words
        lineLeft = self.generateFactsForFixedWords(lineLeft, None)
        # Generate facts for keys
        lineLeft = self.generateFactsForKeys(lineLeft, currFactsNode)

        # 5. Form listGrpEntryKey
        for keyNode in self.keyNodes:
            listGrpEntryKeyParts.append(currFactsNode.get(keyNode.ansibleName))

        # 6. Generate listGrpEntry key
        listGrpEntryKey = Constant.DELIMITER_LIST_KEYS.join(listGrpEntryKeyParts)
        log_vars(listGrpEntryKey=listGrpEntryKey)
        # Locate the list group entry node, if present, generate
        # facts for children alone
        listGrpEntryNode = listGrpCache.get(listGrpEntryKey, None)
        log_vars(listGrpEntryNode=listGrpEntryNode)
        if listGrpEntryNode:
            currFactsNode = listGrpEntryNode

        # 6. Rest of the line parts will be named parameter group,
        #    hence, process two tokens together
        if lineLeft:
            self.generateFactsForChildren(lineLeft, currFactsNode,
                                          negateFlag=negateFlag)

        # 7. Add temp entry node into list node
        if not listGrpEntryNode:
            listFactsNodeVal.append(currFactsNode)
            listGrpCache.update({listGrpEntryKey: currFactsNode})

        return currFactsNode

    def generateCommandForChildren(self, parentFacts, currentFacts,
                                   commonParts, parentCommandParts,
                                   state):
        # Internal method to convert command from all parts
        def convertToCommandInternal(commandParts, commonParts, parentCommandParts, state):
            command = None
            parts = list()

            log_vars(commandParts=commandParts, commonParts=commonParts, parentCommandParts=parentCommandParts)

            if not commandParts:
                return command

            parts.extend(parentCommandParts)
            parts.extend(commonParts)

            if isinstance(commandParts, list):
                if commandParts[0] == Constant.CLI_COMMAND_NO_KEYWORD_TOKEN:
                    if state != Constant.STATE_DELETED:
                        commandParts.remove(Constant.CLI_COMMAND_NO_KEYWORD_TOKEN)
                        parts.extend(commandParts)
                        parts.insert(0, Constant.CLI_COMMAND_NO_KEYWORD_TOKEN)
                    else:
                        commandParts.remove(Constant.CLI_COMMAND_NO_KEYWORD_TOKEN)
                        parts.extend(commandParts)
                else:
                    parts.extend(commandParts)
            else:
                parts.append(commandParts)

            if state == Constant.STATE_DELETED:
                negateCommand(parts)

            command = convertToCommand(parts)

            return command

        # Method starts here
        commands = list()
        # 6. For each children in item,
        for key, child in self.children.items():
            commandParts = list()
            commandPartsTmp = child.generateCommandParts(currentFacts,
                                                         currentFacts,
                                                         state)
            log_vars(commandPartsTmp=commandPartsTmp)
            if not commandPartsTmp:
                continue

            # Node child will return list of list with all its children generated
            if isinstance(commandPartsTmp, list) and isinstance(commandPartsTmp[0], list):
                for partsTmp in commandPartsTmp:
                    command = convertToCommandInternal(partsTmp, commonParts, parentCommandParts, state)
                    commands.append(command)
            else:
                command = convertToCommandInternal(commandPartsTmp, commonParts, parentCommandParts, state)
                commands.append(command)

        log_vars(commands=commands)
        return commands

    def generateMergeCommandsInternal(self, parentFacts, currentFacts,
                                      includeDiff=False, includeMatch=False,
                                      includeHaveOnly=False):
        commands = list()

        parentCommandParts = self.getParentCommandParts(reverse=True)

        for key, item in currentFacts.items():
            log(f"Processing {key}")
            diffNode = None
            matchNode = None
            haveOnlyNode = None
            childCommandPresent = False
            # Create temp command string parts
            commandParts = list()
            commandParts.extend(parentCommandParts)
            commonParts = self.generateCommonCommandParts(item, key, Constant.STATE_MERGED)
            commandParts.extend(commonParts)
            # Generate command parts for children and append
            commandsTmp = self.generateCommandForChildren(currentFacts,
                                                          item,
                                                          commonParts,
                                                          parentCommandParts,
                                                          Constant.STATE_MERGED)
            if commandsTmp:
                childCommandPresent = True
                commands.extend(commandsTmp)
            # Get diff node matching the key of current item
            if includeDiff and parentFacts.diff:
                diffNode = parentFacts.diff.pop(key, None)
            if diffNode:
                commandsTmp = self.generateCommandForChildren(currentFacts,
                                                              diffNode,
                                                              commonParts,
                                                              parentCommandParts,
                                                              Constant.STATE_MERGED)
                if commandsTmp:
                    childCommandPresent = True
                    commands.extend(commandsTmp)
            # Get match node matching the key of current item
            if includeMatch and parentFacts.match:
                matchNode = parentFacts.match.pop(key, None)
            if matchNode:
                commandsTmp = self.generateCommandForChildren(currentFacts,
                                                              matchNode,
                                                              commonParts,
                                                              parentCommandParts,
                                                              Constant.STATE_MERGED)
                if commandsTmp:
                    childCommandPresent = True
                    commands.extend(commandsTmp)
            # Get haveOnly node matching the key of current item
            if includeHaveOnly and parentFacts.haveOnly:
                haveOnlyNode = parentFacts.haveOnly.pop(key, None)
            if haveOnlyNode:
                commandsTmp = self.generateCommandForChildren(currentFacts,
                                                              haveOnlyNode,
                                                              commonParts,
                                                              parentCommandParts,
                                                              Constant.STATE_MERGED)
                if commandsTmp:
                    childCommandPresent = True
                    commands.extend(commandsTmp)

            # 7. Form command string with joining all parts with SPACE
            # if not childCommandPresent:
            #     command = convertToCommand(commandParts)
            #     commands.append(command)
            #     log_vars(command=command)

        return commands

    def generateDeleteCommandsInternal(self, parentFacts, currentFacts,
                                       parentCommand, config,
                                       includeHaveOnly=False, removedKeys=None):
        commands = list()
        log_vars(removedKeys=removedKeys)
        # 1. Create temp command string parts
        commandParts = list()
        parentCommandParts = self.getParentCommandParts(reverse=True)
        negateCommand(parentCommandParts)
        # 2. Get all parent nodes' cliName & append to command string parts
        # 3. Reverse temp command string parts
        # 4. Insert "no" keyword at begining to temp command string parts
        if currentFacts:
            for key, item in currentFacts.items():
                childCommandPresent = False
                haveOnlyNode = None
                log(f"Processing {key}")
                if removedKeys and key in removedKeys:
                    continue
                # Create temp command string parts
                commandParts = list()
                commandParts.extend(parentCommandParts)
                commonParts = self.generateCommonCommandParts(item, key, Constant.STATE_DELETED)
                commandParts.extend(commonParts)
                # Generate command parts for children and append
                commandsTmp = self.generateCommandForChildren(currentFacts,
                                                              item,
                                                              commonParts,
                                                              parentCommandParts,
                                                              Constant.STATE_DELETED)
                if commandsTmp:
                    childCommandPresent = True
                    commands.extend(commandsTmp)

                # Get haveOnly node matching the key of current item
                if includeHaveOnly and parentFacts.haveOnly:
                    haveOnlyNode = parentFacts.haveOnly.pop(key, None)
                if haveOnlyNode:
                    commandsTmp = self.generateCommandForChildren(currentFacts,
                                                                  haveOnlyNode,
                                                                  commonParts,
                                                                  parentCommandParts,
                                                                  Constant.STATE_DELETED)
                if commandsTmp:
                    childCommandPresent = True
                    commands.extend(commandsTmp)

            # 7. Form command string with joining all parts with SPACE
                # if not childCommandPresent:
                #     command = convertToCommand(commandParts)
                #     commands.append(command)
                #     log_vars(command=command)
                #     if removedKeys:
                #         removedKeys.append(key)

        return commands

    def generateDeleteCommands(self, parentFacts, currentFacts,
                              parentCommand, config, removedKeys=None):
        """
        @brief Generate config from the facts (state : deleted)
               for ListGroupNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        """
        # 5. If fixedWords is present,
        #    5.1 apppend all fixed keywords to temp command string parts
        # 6. For each positional keys,
        #    6.1 Locate respective facts node
        #    6.2 Fetch ansibleValue & append to temp command string parts
        # 7. Form command string with joining all parts with SPACE
        # 8. Create ConfigLine instance with command string and add to config
        commands = self.generateDeleteCommandsInternal(currentFacts,
                                                       currentFacts.match,
                                                       parentCommand, config,
                                                       removedKeys=removedKeys)
        addToConfig(config, commands, parentCommand)

    def generateDeleteAllCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : deleted)
               for ListGroupNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        """
        removedKeys = list()
        # Generate delete for match nodes
        super().generateDeleteCommandsInternal(currentFacts.match, parentCommand,
                                               config, removedKeys=removedKeys)
        # Generate delete for diff nodes
        super().generateDeleteCommandsInternal(currentFacts.diff, parentCommand,
                                               config, removedKeys=removedKeys)
        # Generate delete for haveOnly nodes
        super().generateDeleteCommandsInternal(currentFacts.haveOnly, parentCommand,
                                               config, removedKeys=removedKeys)

    def generateReplaceCommandsHaveOnly(self, parentFacts, currentFacts):
        commands = list()
        # 1. Create temp command string parts
        commandParts = list()
        parentCommandParts = self.getParentCommandParts(reverse=True)
        negateCommand(parentCommandParts)
        # 2. Get all parent nodes' cliName & append to command string parts
        # 3. Reverse temp command string parts
        # 4. Insert "no" keyword at begining to temp command string parts
        if currentFacts:
            for key, item in currentFacts.items():
                childCommandPresent = False
                matchNode = None
                commandsTmp = None
                log(f"Processing {key}")
                # Create temp command string parts
                commandParts = list()
                commandParts.extend(parentCommandParts)
                commonParts = self.generateCommonCommandParts(item, key, Constant.STATE_DELETED)
                commandParts.extend(commonParts)
                # Get match node matching the key of current item
                if parentFacts.match:
                    matchNode = parentFacts.match.pop(key, None)
                if matchNode:
                    commandsTmp = self.generateCommandForChildren(currentFacts,
                                                                  matchNode,
                                                                  commonParts,
                                                                  parentCommandParts,
                                                                  Constant.STATE_DELETED)
                if commandsTmp:
                    commands.extend(commandsTmp)

        return commands


    def generateReplaceCommandsInternal(self, parentFacts, currentFacts,
                                      includeDiff=False):
        commands = list()

        # Parent commands for merge
        parentCommandParts = self.getParentCommandParts(reverse=True)
        # Parent commands for delete
        parentCommandPartsTmp = list()
        parentCommandPartsTmp.extend(parentCommandParts.copy())
        negateCommand(parentCommandParts)

        for key, item in currentFacts.items():
            log(f"Processing {key}")
            diffNode = None
            haveOnlyNode = None
            childCommandPresent = False
            # Create temp command string parts
            commandParts = list()
            commandParts.extend(parentCommandParts)
            commonParts = self.generateCommonCommandParts(item, key, Constant.STATE_REPLACED)
            commandParts.extend(commonParts)
            # Generate command parts for children and append
            commandsTmp = self.generateCommandForChildren(currentFacts,
                                                          item,
                                                          commonParts,
                                                          parentCommandParts,
                                                          Constant.STATE_REPLACED)
            if commandsTmp:
                childCommandPresent = True
                commands.extend(commandsTmp)
            # Get diff node matching the key of current item
            if includeDiff and parentFacts.diff:
                diffNode = parentFacts.diff.pop(key, None)
            if diffNode:
                commandsTmp = self.generateCommandForChildren(currentFacts,
                                                              diffNode,
                                                              commonParts,
                                                              parentCommandParts,
                                                              Constant.STATE_REPLACED)
                if commandsTmp:
                    childCommandPresent = True
                    commands.extend(commandsTmp)

            # Get haveOnly node matching the key of current item
            if parentFacts.haveOnly:
                haveOnlyNode = parentFacts.haveOnly.pop(key, None)
            if haveOnlyNode:
                commandsTmp = self.generateCommandForChildren(currentFacts,
                                                              haveOnlyNode,
                                                              commonParts,
                                                              parentCommandPartsTmp,
                                                              Constant.STATE_DELETED)
                if commandsTmp:
                    childCommandPresent = True
                    commands.extend(commandsTmp)

            # 7. Form command string with joining all parts with SPACE
            # if not childCommandPresent:
            #     command = convertToCommand(commandParts)
            #     commands.append(command)
            #     log_vars(command=command)

        return commands


    def generateReplaceCommands(self, parentFacts, currentFacts,
                                parentCommand, config):
        """
        @brief Generate config from the facts (state : deleted)
               for ListGroupNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        """
        # Ignore nodes that are present in match only
        self.ignoreMatchOnlyNodes(currentFacts)

        # Generate replace for want-only & diff nodes
        commands = list()
        # 1. Iterate all keys in want-only facts, for each item
        if currentFacts.wantOnly:
            log(f"Processing wantOnly nodes")
            commandsTmp = self.generateReplaceCommandsInternal(currentFacts,
                                                             currentFacts.wantOnly,
                                                             includeDiff=True)
            commands.extend(commandsTmp)

        # 1. Iterate all keys in diff facts, for each item
        if currentFacts.diff:
            log(f"Processing diff nodes")
            commandsTmp = self.generateReplaceCommandsInternal(currentFacts,
                                                             currentFacts.diff)
            commands.extend(commandsTmp)

        # Delete haveOnly children for matching with match facts
        if currentFacts.haveOnly:
            log(f"Processing haveOnly nodes")
            commandsTmp = self.generateReplaceCommandsHaveOnly(currentFacts,
                                                               currentFacts.haveOnly)
            commands.extend(commandsTmp)

        # 8. Create ConfigLine instance with command string and add to config
        addToConfig(config, commands, parentCommand)

    def generateOverriddenCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : overridden)
               for ListNGroupode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        """
        # currentFacts.dump()

        # Ignore nodes that are present in match only
        self.ignoreMatchOnlyNodes(currentFacts)

        # Generate replace for want-only & diff nodes
        self.generateReplaceCommands(parentFacts, currentFacts, parentCommand, config)

        # Generate delete for have-only nodes
        commands = self.generateDeleteCommandsInternal(currentFacts,
                                                       currentFacts.haveOnly,
                                                       parentCommand, config)
        # 8. Create ConfigLine instance with command string and add to config
        addToConfig(config, commands, parentCommand)

# Mode node
class ModeNode(Node):

    # Methods
    def __init__(self, parent=None, name=None):
        super().__init__(parent=parent)
        # Members
        self._name = name
        self._cmdNode = None
        self._cmdToSearch = list()
        self._subCmdsToSearch = list()
        # super().children as subcommands
        self._subModes = dict()

    @property
    def cmdNode(self):
        return self._cmdNode

    @cmdNode.setter
    def cmdNode(self, value):
        self._cmdNode = value

    @property
    def cmdToSearch(self):
        return self._cmdToSearch

    @cmdToSearch.setter
    def cmdToSearch(self, value):
        self._cmdToSearch = value

    @property
    def subModes(self):
        return self._subModes

    @subModes.setter
    def subModes(self, value):
        self._subModes = value

    @property
    def subCmdsToSearch(self):
        return self._subCmdsToSearch

    @subCmdsToSearch.setter
    def subCmdsToSearch(self, value):
        self._subCmdsToSearch = value

    def dump(self):
        """
        @brief Print members of ModeNode class
        """
        # log(f"ModeNode")
        log_vars(name=self.name)
        if self.cmdNode:
            log(f"cmdNode of {self.name}")
            self.cmdNode.dump()
        log(f"subCommands of {self.name}")
        self.dumpChildren()
        if self.subModes:
            log(f"subModes of {self.name}")
            for key, subMode in self.subModes.items():
                subMode.dump()

    def addSubMode(self, key, obj):
        self._subModes.update({key: obj})

    def isDeleteCmdNode(self, facts):
        """
        @brief Check whether current node's cmdNode can be deleted or not
               Logic: If facts contain nodes for any subcommands or nodes
                      for submodes, cmdNode cannot be removed

        @param facts (Facts): Facts object of respective node

        @returns result (bool)
        """

        result = True

        if self.isChildPresent(facts):
            result = False

        # Return if not True
        if not result: return result

        # 2. Iterate all submodes
        for key, subMode in self.subModes.items():
            # log(f"Check SubMode {subMode.cmdNode.ansibleName}")
        # 2.2. If factsNode is present in wantOnly or match or diff,
        #      set result as False and break
            factsTmp = facts.find(subMode.cmdNode.ansibleName)
            if factsTmp and (factsTmp.wantOnly or factsTmp.match or factsTmp.diff):
                # log(f"SubMode {subMode.cmdNode.ansibleName} is present")
                result = False
                break

        return result

    def buildSubCmdNodeKey(self, command):
        """
        @brief Build key for subcommand node to add into children
               Required to prevent duplicates
               Logic: Combine all CLI keywords to find unique name

        @param command (str): Command syntax

        @returns result(str): Key to be used while adding subCommand
                              into children
        """
        # 1. Form temp command string parts list
        result = ''
        commandKeyParts = list()
        # 2. Split the command with DELIMITER_CLI_COMMAND_WORD
        commandParts = command.split(Constant.DELIMITER_CLI_COMMAND_WORD)
        log_vars(commandParts=commandParts)
        commandPartsIt = enumerate(commandParts)
        # 3. Iterate all parts
        token = next(commandPartsIt, None)
        while token:
            ansibleWord = None
            log_vars(token=token)
            tokenVal = token[1]
            if isParamNode(tokenVal):
                break
        # 4. Extract CLI keywords alone
            if Constant.INDICATOR_ANSIBLE_WORD in tokenVal:
                tokenValParts = tokenVal.split(Constant.INDICATOR_ANSIBLE_WORD)
                cliWord = tokenValParts[0]
                ansibleWord = tokenValParts[1]
            else:
                cliWord = tokenVal

            # Break when optional parameter is found
            if ansibleWord and hasOptional(ansibleWord):
                break

        # 5. Add CLI keyword into temp command string parts
            commandKeyParts.append(cliWord)
        # 6. Continue Step 4 & 5 until either parameter node is found or
        #    end of list
            token = next(commandPartsIt, None)
        # 7. Join all command string parts with DELIMITER_CLI_COMMAND_WORD
        result = convertToCommand(commandKeyParts)
        # 8. Return the computed command string
        log_vars(command=command, result=result)
        return result

    def buildTree(self, mode, listCache):
        """
        @brief Build tree for ModeNode class

        @param lines (dict): Dict contains details about the mode
        @param listCache (dict): Placeholder to update all list nodes
                                 required for compress & expand facts

        @returns None
        """
        # Format of mode in reference line
        # <mode>:
        #   command: <command that opens mode in CLI>
        #   subcommands:
        #     - <list of subcommands under in current mode>
        #   submodes:
        #     <submode>:
        #       <Repeats the same convention as mode>
        #     <submode>:
        #       <Repeats the same convention as mode>
        # 1. Check whether command is present, if so
        if Constant.COMMAND_INDICATOR in mode:
            line = mode.get(Constant.COMMAND_INDICATOR, None)
        #    1.1 Create corresponding node instance
        #    1.2 Save new node in cmdNode
            self.cmdNode, lineLeft = self.createTreeNode(line)
        #    1.3 Invoke buildTree of cmdNode with command node value
            self.cmdNode.buildTree(lineLeft, listCache)
        # 2. Check whether subcommands is present, if so
        if Constant.SUBCOMMAND_INDICATOR in mode:
            listGrpCache = dict()
            subCmds = mode.get(Constant.SUBCOMMAND_INDICATOR, None)
        #    2.1 Iterate all subcommands
            for subCmd in subCmds:
        #    2.2 Create respective node
                subCmdNodeKey = self.buildSubCmdNodeKey(subCmd)
        #    2.3 Create respective node
                log_vars(listGrpCache=listGrpCache)
                subCmdObj, lineLeft = self.createTreeNode(subCmd,
                                                  listGrpCache=listGrpCache)
        #    2.4 Append new node into chilldren member
                self.addChild(subCmdNodeKey, subCmdObj)
        #    2.5 Invoke buildTree for each new node with its value
                log_vars(listCache=listCache)
                subCmdObj.buildTree(lineLeft, listCache)
        # 3. Iterate mode dict, key values except command & subcommands
        #    are submodes, for each submode
        for key, value in mode.items():
            if key != Constant.COMMAND_INDICATOR and \
               key != Constant.SUBCOMMAND_INDICATOR:
        #    3.1 Create new object of ModeNode
                modeObj = ModeNode(name=key, parent=self)
        #    3.2 Append new node into submodes
                self.addSubMode(key, modeObj)
        #    3.3 Invoke buildTree of new node with its value
                modeObj.buildTree(value, listCache)

    def buildCmdsToSearch(self):
        """
        @brief Build commands to search for while generating facts
               for ModeNode class

        @param None

        @returns None
        """
        # 1. If cmdNode is present,
        if self.cmdNode:
        #    1.1 invoke buildCmdsToSearch for cmdNode,
        #        pass cmdToSearch as argument to collect the commands
            tmpList = list()
            self.cmdNode.buildCmdsToSearch(tmpList)
            if tmpList:
                self.cmdToSearch = tmpList.pop()
        # 2. If subcommands is present,
        if self.children:
        #    2.1 Iterate all subcommands
            for key, subCmd in self.children.items():
        #    2.2 Invoke buildCmdsToSearch for each subcommand,
        #        pass subCmdsToSearch as argument to collect the commands
                subCmd.buildCmdsToSearch(self.subCmdsToSearch)
        # 3. If submodes is not empty,
        if self.subModes:
        #    3.1 Iterate all submodes
            for key, subMode in self.subModes.items():
        #    3.2 Invoke buildCmdsToSearch for each submode
                subMode.buildCmdsToSearch()
        log_vars(name=self.name, cmdToSearch=self.cmdToSearch)
        log_vars(name=self.name, subCmdsToSearch=self.subCmdsToSearch)


    def generateFactsForSubCmds(self, config, facts):
        """
        @brief Generate facts from the config for ModeNode class

        @param config (ConfigLine): Configurations to be converted as facts
        @param facts (dict): Placeholder to update the facts

        @returns None
        """
        listGrpCache = dict()
        # 1. Iterate all children in config, for each child in config
        for childConfig in config.child_objs:
        # 1.1 Skip if the child has children as it belongs to submode
            if childConfig.has_children: continue
        # 1.2 If above condition is not true, find matching subcommand node
            for key, subCmd in self.children.items():
                line = childConfig.text
                log(f"Processing {line}, {key}")
        #    1.2.1. Find respective subcommand by matching command text
                if line.startswith(key + Constant.DELIMITER_CLI_COMMAND_WORD) or \
                   line == key or \
                   line.startswith(Constant.CLI_COMMAND_NO_KEYWORD_TOKEN + \
                                   Constant.DELIMITER_CLI_COMMAND_WORD + \
                                   key + \
                                   Constant.DELIMITER_CLI_COMMAND_WORD):
        #    1.2.2. Call generateFacts with subcommand node
                    subCmd.generateFacts(line, facts,
                                         listGrpCache=listGrpCache)


    def generateFactsForSubModes(self, config, facts):
        """
        @brief Generate facts from the config for ModeNode class

        @param config (ConfigLine): Configurations to be converted as facts
        @param facts (dict): Placeholder to update the facts

        @returns None
        """
        # 1. Iterate all children in config, for each child in config
        for childConfig in config.child_objs:
        # 1.1 Skip if the child has NO children as it belongs to subcommand
            if not childConfig.has_children: continue
        # 1.2 If above condition is not true, find matching submode node
            for key, subMode in self.subModes.items():
        #    1.2.1. Find respective subcommand by matching command text
                line = childConfig.text
                if line.startswith(subMode.cmdToSearch + Constant.DELIMITER_CLI_COMMAND_WORD) or \
                   line == subMode.cmdToSearch:
                    log_vars(key=key, text=line, cmdToSearch=subMode.cmdToSearch)
        #    1.2.2. Call generateFacts with subcommand node
                    subMode.generateFacts(childConfig, facts)

    def generateFactsForSubmodeInternal(self, config, facts):
        """
        @brief Generate facts from the config for ModeNode calls

        @param config (ConfigLine): Configurations to be converted as facts
        @param facts (dict): Placeholder to update the facts

        @returns None
        """
        configItems = list()
        # 1. If cmdNode is present
        if self.cmdNode:
        #    1.1. Filter all matching config against cmdToSearch
            for item in config.child_objs:
                line = item.text
                if line.startswith(self.cmdToSearch + Constant.DELIMITER_CLI_COMMAND_WORD) or \
                   line == self.cmdToSearch:
                    configItems.append(item)
        #    1.2. Iterate each matching config
            for configItem in configItems:
                configItemText = configItem.line
                configItemChildren = configItem.children
                configItemParent = configItem.parents
                log_vars(configItemParent=configItemParent,
                             configItemText=configItemText,
                             configItemChildren=configItemChildren)
        #    1.3 call generateFacts for cmdNode,
        #        return value indicates new Facts created recently,
        #        shall be used susequently for subcommands and submodes
                cmdFactsObj = self.cmdNode.generateFacts(configItem.text, facts)
        #    1.4. Find respective subcommand by matching command text
        #    1.5. Call generateFacts for subcommand
                self.generateFactsForSubCmds(configItem, cmdFactsObj)
        #    1.6. Call generateFacts for submodes
                self.generateFactsForSubModes(configItem, cmdFactsObj)
        # 2. If cmdNode is not present - shall not occur, error case
        else:
            # TODO : Throw error
            log(f"Command node is empty for subMode {self.name}")
            pass

    def findMatchingCommands(self, config):
        result = list()

        if isinstance(config, SonicNetworkConfig):
            result = config.get_object_partial([self.cmdToSearch], False)
        elif  isinstance(config, ConfigLine):
            result.append(config)
        else:
            pass

        return result

    def findMatchingChild(self, config):
        """
        @brief Find matching child node from command string
               for ModeNode class

        @param config (NetworkConfig or str): Config to be used for search
        @param config (str): Command string text

        @returns result (object): Matching subcommand node
        """
        result = None

        log_vars(config=config)

        # Return when config is empty
        if not config:
            return result

        # 1. Get command string text
        if isinstance(config, str):
            line = config
        else:
            line = config.text
        # 2. Iterate all child nodes
        for key, node in self.children.items():
        # 3. Check whether child's key pattern is present in command string
        # Append SPACE with key pattern for exact match
            if line.startswith(key + Constant.DELIMITER_CLI_COMMAND_WORD) or \
               line == key:
                result = node
                break
        # 4. Return the result, if match is found
        return result

    def generateFacts(self, config, facts):
        """
        @brief Generate facts from the config for ModeNode class

        @param config (NetworkConfig): Configurations to be converted as facts
        @param facts (dict): Placeholder to update the facts

        @returns None
        """
        # TODO: Reuse super() method whereever possible
        # 1. Derive cmdsToSearch of parent nodes
        # 2. If cmdNode is present
        if self.cmdNode:
        #    2.1 Iterate all cmdToSearch items, for each item
        #    2.2. Form finalCmdToSearch, call get_parial_block
            configItems = self.findMatchingCommands(config)
        #    2.3. Iterate each config from above return value
            for configItem in configItems:
                configItemText = configItem.line
                configItemChildren = configItem.children
                configItemParent = configItem.parents
                log_vars(configItemParent=configItemParent,
                             configItemText=configItemText,
                             configItemChildren=configItemChildren)
        #    2.5 call generateFacts for cmdNode,
        #        return value indicates new Facts created recently,
        #        shall be used susequently for subcommands and submodes
                cmdFactsObj = self.cmdNode.generateFacts(configItem.text, facts)
        #    2.6. Find respective subcommand by matching command text
        #    2.7. Call generateFacts for subcommand
                self.generateFactsForSubCmds(configItem, cmdFactsObj)
        #    1.6. Call generateFacts for submodes
                self.generateFactsForSubModes(configItem, cmdFactsObj)
        # 3. If cmdNode is not present
        else:
            listGrpCache = dict()
        #    3.1 Iterate all subCmdsToSearch items, for each item
            log_vars(subCmdsToSearch=self.subCmdsToSearch)
            for cmdToSearch in self.subCmdsToSearch:
        #    3.2. Call get_parial_config
                configItems = config.get_object_partial([cmdToSearch], False)
                log_vars(configItems=configItems)
        #    3.3. Iterate each config from above return value
                for configItem in configItems:
                    log_vars(configItem=configItem)
        #    3.4. Find respective subcommand by matching command text
                    subCmd = self.findMatchingChild(configItem)
        #    3.5. Call generateFacts
                    if subCmd:
                        subCmd.generateFacts(configItem.text, facts,
                                             listGrpCache=listGrpCache)

    def generateCommandForChildren(self, parentFacts, currentFacts,
                                   parentCommand, config, state):
        # if parentFacts:
        #     log(f"parentFacts")
        #     parentFacts.dump()
        # if currentFacts:
        #     log(f"currentFacts")
        #     currentFacts.dump()
        log_vars(parentCommand=parentCommand, state=state)
        # 6. For each children in item,
        for key, child in self.children.items():
            log(f"Processing {key}")
        #    6.1 Locate respective facts node
            if not isinstance(child, SkipNode):
                factsNode = currentFacts.find(child.ansibleName)
            else:
                factsNode = currentFacts
            # log("factsNode")
            # factsNode.dump()
        #    6.2 Append cliName and ansibleValue to temp command string parts
            if not factsNode: continue
            if state == Constant.STATE_MERGED:
                child.generateMergeCommands(currentFacts, factsNode,
                                            parentCommand, config)
            elif state == Constant.STATE_DELETED:
                child.generateDeleteCommands(currentFacts, factsNode,
                                            parentCommand, config)
            elif state == Constant.STATE_REPLACED:
                child.generateReplaceCommands(currentFacts, factsNode,
                                            parentCommand, config)
            elif state == Constant.STATE_OVERRIDDEN:
                child.generateOverriddenCommands(currentFacts, factsNode,
                                            parentCommand, config)
            else:
                # TODO: Throw error
                log(f"Unknown state {state}")

    def generateCommandForSubmode(self, parentFacts, currentFacts,
                                   parentCommand, config, state):
        # if parentFacts:
        #     log(f"parentFacts")
        #     parentFacts.dump()
        # if currentFacts:
        #     log(f"currentFacts")
        #     currentFacts.dump()
        log_vars(parentCommand=parentCommand, state=state)
        # 6. For each children in item,
        for key, subMode in self.subModes.items():
            log(f"Processing {key}")
        #    6.1 Locate respective facts node
            factsNode = currentFacts.find(subMode.cmdNode.ansibleName)
        #    6.2 Append cliName and ansibleValue to temp command string parts
            if not factsNode: continue
            if state == Constant.STATE_MERGED:
                subMode.generateMergeCommands(parentFacts, currentFacts,
                                            parentCommand, config)
            elif state == Constant.STATE_DELETED:
                subMode.generateDeleteCommands(parentFacts, currentFacts,
                                            parentCommand, config)
            elif state == Constant.STATE_REPLACED:
                subMode.generateReplaceCommands(parentFacts, currentFacts,
                                            parentCommand, config)
            elif state == Constant.STATE_OVERRIDDEN:
                subMode.generateOverriddenCommands(parentFacts, currentFacts,
                                            parentCommand, config)
            else:
                # TODO: Throw error
                log(f"Unknown state {state}")

    def generateModeCommand(self, node, key, parentCommand, config):
        modeCommand = None
        modeCommand = self.cmdNode.generateModeCommand(node, key)
        log_vars(modeCommand=modeCommand)
        addToConfig(config, modeCommand, parentCommand)

        return modeCommand

    def generateModeDeleteCommand(self, node, key, parentCommand, config):
        modeCommand = None
        modeCommand = self.cmdNode.generateModeDeleteCommand(node, key)
        log_vars(modeCommand=modeCommand)
        addToConfig(config, modeCommand, parentCommand)

        return modeCommand

    def generateMergeCommandsInternal(self, parentFacts, currentFacts,
                                      config, parentCommand,
                                      includeDiff=False, includeMatch=False,
                                      includeHaveOnly=False):
        for key, item in currentFacts.items():
            log(f"Processing {key}")
            currNode = None
            diffNode = None
            matchNode = None
            currNode = parentFacts.find(key)
            parentCommandTmp = list()
            if parentCommand:
                parentCommandTmp.extend(parentCommand)
            modeCommand = self.generateModeCommand(item, key, parentCommand, config)

            # Skip processing this entry if modeCommand is not formed
            if not modeCommand:
                continue

            parentCommandTmp.append(modeCommand)
            # Generate command parts for children and append
            self.generateCommandForChildren(parentFacts, currNode, parentCommandTmp, config, Constant.STATE_MERGED)
            self.generateCommandForSubmode(parentFacts, currNode, parentCommandTmp, config, Constant.STATE_MERGED)
            # Get diff node matching the key of current item
            if includeDiff and parentFacts.diff:
                diffNode = parentFacts.diff.pop(key, None)
            if diffNode:
                self.generateCommandForChildren(parentFacts, diffNode, parentCommandTmp, config, Constant.STATE_MERGED)
                self.generateCommandForSubmode(parentFacts, diffNode, parentCommandTmp, config, Constant.STATE_MERGED)


    def generateMergeCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : merged)
               for ModeNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        @returns None
        """

        # 1. cmdNode is present
        #   1.1. Iterate all keys in want-only facts, for each item
        #   1.2. Call generateMergeSingleEntry with item
        #   1.3. Save command as parentCommand
        #   1.4. Add command list into config with parentCommand
        #   - For each subcommand, find respective factsNode
        #   - Call generateMergeCommands with parentCommand and factsNode
        #   - For each submode, find respective factsNode
        #   - Call generateMergeCommands with parentCommand and factsNode
        #   1.5. Iterate all keys in diff
        #   1.6. Call generateMergeSingleEntry with diffNode alone
        #   1.7. Add command list into config with parentCommand
        #   - For each subcommand, find respective factsNode
        #   - Call generateMergeCommands with parentCommand and factsNode
        #   - For each submode, find respective factsNode
        #   - Call generateMergeCommands with parentCommand and factsNode

        #       1.2.4. Start processing subcommands (children)
        #       1.2.5. For each subcommand, check if it is present in wantOnly
        #              If present, locate the node, call generateMergeCommands
        #              for that node, pass parentCmd
        #       1.2.6. For each subcommand, check if it is present in diff
        #              If present, locate the node, call generateMergeCommands
        #              for that node, pass parentCmd
        #       1.2.7. Start processing submodes (subModes)
        #       1.2.8. For each submode, call generateMergeCommands
        #              for that node, pass parentCmd
        #   1.3. If cmdNode is not class of ListNode
        #       1.3.1. Call generateMergeCommands for cmdNode
        #              with above factsNode
        # 2. cmdNode is absent
        #   2.1. Iterate all subcommands (children), for each subcommand
        #       1.2.5. For each subcommand, check if it is present in wantOnly
        #              If present, locate the node, call generateMergeCommands
        #              for that node, pass parentCmd
        #       1.2.5. For each subcommand, check if it is present in diff
        #              If present, locate the node, call generateMergeCommands
        #              for that node, pass parentCmd
        # 1. If cmdNode is present
        log_vars(parentCommand=parentCommand)
        if self.cmdNode:
            modeCommand = None
            factsCmdNode = currentFacts.find(self.cmdNode.ansibleName)
            # Return when factsCmdNode is empty
            if not factsCmdNode: return
            if isinstance(self.cmdNode, ListNode):
                # 1. Iterate all keys in want-only facts, for each item
                if factsCmdNode.wantOnly:
                    log(f"Processing wantOnly nodes")
                    for key, item in factsCmdNode.wantOnly.items():
                        diffNode = None
                        log(f"Processing {key}")
                        nodeTmp = factsCmdNode.find(key)
                        parentCommandTmp = list()
                        if parentCommand:
                            parentCommandTmp.extend(parentCommand)
                        modeCommand = self.generateModeCommand(item, key, parentCommand, config)
                        # Skip processing this entry if modeCommand is not formed
                        if not modeCommand:
                            continue

                        parentCommandTmp.append(modeCommand)
                        # Generate command parts for children and append
                        self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_MERGED)
                        self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_MERGED)
                        # Get diff node matching the key of current item
                        if factsCmdNode.diff:
                            diffNode = factsCmdNode.diff.pop(key, None)
                        if diffNode:
                            self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_MERGED)
                            self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_MERGED)
                        self.cmdNode.generateExitCmd(parentCommandTmp, config)

                # 1. Iterate all keys in diff facts, for each item
                if factsCmdNode.diff:
                    log(f"Processing diff nodes")
                    for key, item in factsCmdNode.diff.items():
                        log(f"Processing {key}")
                        nodeTmp = factsCmdNode.find(key)
                        parentCommandTmp = list()
                        if parentCommand:
                            parentCommandTmp.extend(parentCommand)
                        modeCommand = self.generateModeCommand(item, key, parentCommand, config)
                        # Skip processing this entry if modeCommand is not formed
                        if not modeCommand:
                            continue

                        parentCommandTmp.append(modeCommand)
                        # Generate command parts for children and append
                        self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_MERGED)
                        self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_MERGED)
                        self.cmdNode.generateExitCmd(parentCommandTmp, config)
            # cmdNode is not list
            else:
                # 1. Iterate all keys in want-only facts, for each item
                if factsCmdNode.wantOnly:
                    diffNode = None
                    nodeTmp = factsCmdNode.find(key)
                    parentCommandTmp = list()
                    if parentCommand:
                        parentCommandTmp.extend(parentCommand)
                    modeCommand = self.generateModeCommand(item, key, parentCommand, config)
                    # Skip processing this entry if modeCommand is not formed
                    if not modeCommand:
                        return

                    parentCommandTmp.append(modeCommand)
                    # Generate command parts for children and append
                    self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_MERGED)
                    self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_MERGED)
                    # Get diff node matching the key of current item
                    if factsCmdNode.diff:
                        diffNode = factsCmdNode.diff.pop(key, None)
                    if diffNode:
                        self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_MERGED)
                        self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_MERGED)
        # 2. If cmdNode is not present,
        else:
            self.generateCommandForChildren(parentFacts, currentFacts, parentCommand, config, Constant.STATE_MERGED)
        #    2.1 Iterate all children, for each children
        #    2.2 Locate the node in currentFacts
        #    2.3 Call generateMergeCommands() with above facts node

    def generateDeleteAllModeCommands(self, currentFacts,
                               parentCommand, config):
        facts = currentFacts.get(self.cmdNode.ansibleName, None)
        if not facts:
            return

        for key, item in facts.items():
            log(f"Processing {key}")
            parentCommandTmp = list()
            if parentCommand:
                parentCommandTmp.extend(parentCommand)
            modeCommand = self.generateModeDeleteCommand(item, key, parentCommand, config)

    def generateDeleteAllForChildren(self, parentFacts, currentFacts,
                              parentCommand, config):
        # 6. For each children in item,
        for key, child in self.children.items():
        #    6.1 Locate respective facts node
            factsNode = currentFacts.find(child.ansibleName)
        #    6.2 Append cliName and ansibleValue to temp command string parts
            if factsNode:
                child.generateDeleteAllCommands(currentFacts, factsNode,
                                                parentCommand, config)

    def generateDeleteAllCommands(self, parentFacts, currentFacts,
                                  parentCommand, config):
        """
        @brief Generate config from the facts (state : deleted)
               for ModeNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        @returns None
        """
        # If cmdNode is absent, deleteAll for children
        if not self.cmdNode:
            self.generateDeleteAllForChildren(parentFacts, currentFacts, parentCommand, config)
            return

        # Delete all for mode based commands
        # Delete match
        if currentFacts.match:
            self.generateDeleteAllModeCommands(currentFacts.match, parentCommand, config)
        # Delete haveOnly
        if currentFacts.haveOnly:
            self.generateDeleteAllModeCommands(currentFacts.haveOnly, parentCommand, config)
        # Delete diff nodes
        if currentFacts.diff:
            self.generateDeleteAllModeCommands(currentFacts.diff, parentCommand, config)


    def generateDeleteCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : deleted)
               for ModeNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config

        @returns None
        """
        # TODO: Revisit the logic of checking subcommands are present or not
        #       Instead, facts node to be checked against subcommands
        # 1. If cmdNode is present
        #   - For delete all case,
        #   - For delete specific case,
        #   - Locate node in match facts
        #   - If mode delete case
        #   - Call generateDeleteCommands for cmdNode, pass parentCommand
        #   - If not mode delete case
        #   - Call generateMergeCommands for cmdNode, pass parentCommand
        # 2. If cmdNode is not present,
        #   - For delete all case (want is empty)
        #   - Iterate all children, locate the node in match facts, call
        #     generateDeleteCommands for the child, pass parentCommand
        #   - Iterate all children, locate the node in have-only facts, call
        #     generateDeleteCommands for the child, pass parentCommand
        #   - For delete specific case,
        #   - Iterate all children, locate the node in match facts, call
        #     generateDeleteCommands for the child, pass parentCommand
        # 1. If cmdNode is present
        if self.cmdNode:
            modeCommand = None
        #    1.1 Locate facts node with ansibleName
            factsCmdNode = currentFacts.find(self.cmdNode.ansibleName)
            # Return when factsCmdNode is empty
            if not factsCmdNode: return
        #    1.2 If above facts node is list,
            if isinstance(self.cmdNode, ListNode):
                if factsCmdNode.match:
                    log(f"Processing match nodes")
                    for key, item in factsCmdNode.match.items():
                        log(f"Processing {key}")
                        nodeTmp = factsCmdNode.find(key)
        #      1.2.1 Check whether mode delete case or not
                        if self.isDeleteCmdNode(nodeTmp):
                            log(f"Mode delete case")
        #      1.2.1.1 Call generateDeleteCommands() for cmdNode
                            modeCommand = self.generateModeDeleteCommand(item, key, parentCommand, config)
        #      1.2.1.2 Continue to process next item
                        else:
                            parentCommandTmp = list()
                            if parentCommand:
                                parentCommandTmp.extend(parentCommand)
                            modeCommand = self.generateModeCommand(item, key, parentCommand, config)
                            # Skip processing this entry if modeCommand is not formed
                            if not modeCommand:
                                continue
                            parentCommandTmp.append(modeCommand)
        #      1.2.1.3 Call generateMergeCommands() for cmdNode
        #      1.2.2 If subcommands are present, delete subcommands case
        #      1.2.2.1 Iterate all subcommands
                            self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_DELETED)
        #        1.2.2.1.1 Call generateDeleteCommands for each list item
                            self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_DELETED)
                            if config.remove_empty_block(modeCommand, parentCommand):
                                modeCommand = None
                            else:
                                self.cmdNode.generateExitCmd(parentCommandTmp, config)
        #      1.2.2.2 Iterate all submodes
        #        1.2.2.2.1 Call generateDeleteCommands for each list item
        #    1.3 If above facts node is NOT list,
            else:
        #      1.3.1 Check whether mode delete case or not
                if self.isDeleteCmdNode(factsCmdNode):
                    log(f"Mode delete case")
        #      1.3.1.1 Call generateDeleteCommands() for cmdNode
                    modeCommand = self.generateModeDeleteCommand(factsCmdNode.match, None, parentCommand, config)
        #      1.3.1.2 Return
                    return
                else:
        #      1.3.1.3 Call generateMergeCommands() for cmdNode
                    nodeTmp = factsCmdNode.find(key)
                    parentCommandTmp = list()
                    if parentCommand:
                        parentCommandTmp.extend(parentCommand)
                    modeCommand = self.generateModeCommand(item, key, parentCommand, config)
                    # Skip processing this entry if modeCommand is not formed
                    if not modeCommand:
                        return

                    parentCommandTmp.append(modeCommand)
        #      1.2.1.3 Call generateMergeCommands() for cmdNode
        #      1.2.2 If subcommands are present, delete subcommands case
        #      1.2.2.1 Iterate all subcommands
                    self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_DELETED)
        #        1.2.2.1.1 Call generateDeleteCommands for each list item
                    self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_DELETED)
        #      1.2.2.2 Iterate all submodes
        #        1.2.2.2.1 Call generateDeleteCommands for each list item
        #    1.3 If above facts node is NOT list,
        # 2. If cmdNode is not present,
        else:
            self.generateCommandForChildren(parentFacts, currentFacts, parentCommand, config, Constant.STATE_DELETED)
        #    2.1 Iterate all children, for each children
        #    2.2 Locate the facts node
        #    2.3 Call generateDeleteCommands() with above facts node


    def generateReplaceCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : replaced)
               for ModeNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config
                             want-only, match, diff, have-only config are included

        @returns None
        """
        # TODO: Revisit the logic of checking subcommands are present or not
        #       Instead, facts node to be checked against subcommands
        #       Logic to separate old and new config from facts to be added
        # 1. If cmdNode is present
        if self.cmdNode:
            modeCommand = None
            factsCmdNode = currentFacts.find(self.cmdNode.ansibleName)
            # Return when factsCmdNode is empty
            if not factsCmdNode: return
            visitedKeys = list()
            if isinstance(self.cmdNode, ListNode):
                # 1. Iterate all keys in want-only facts, for each item
                if factsCmdNode.wantOnly:
                    for key, item in factsCmdNode.wantOnly.items():
                        diffNode = None
                        nodeTmp = factsCmdNode.find(key)
                        parentCommandTmp = list()
                        if parentCommand:
                            parentCommandTmp.extend(parentCommand)
                        modeCommand = self.generateModeCommand(item, key, parentCommand, config)
                        # Skip processing this entry if modeCommand is not formed
                        if not modeCommand:
                            continue
                        parentCommandTmp.append(modeCommand)
                        # Generate command parts for children and append
                        self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_REPLACED)
                        self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_REPLACED)
                        # Get diff node matching the key of current item
                        if nodeTmp.diff:
                            diffNode = nodeTmp.diff.get(key, None)
                        if diffNode:
                            self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_REPLACED)
                            self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_REPLACED)
                            visitedKeys.append(key)
                        self.cmdNode.generateExitCmd(parentCommandTmp, config)

                # 1. Iterate all keys in diff facts, for each item
                #    skip the key if present in visitedKeys
                if factsCmdNode.diff:
                    for key, item in factsCmdNode.diff.items():
                        if key in visitedKeys: continue
                        nodeTmp = factsCmdNode.find(key)
                        parentCommandTmp = list()
                        if parentCommand:
                            parentCommandTmp.extend(parentCommand)
                        modeCommand = self.generateModeCommand(item, key, parentCommand, config)
                        # Skip processing this entry if modeCommand is not formed
                        if not modeCommand:
                            continue
                        parentCommandTmp.append(modeCommand)
                        # Generate command parts for children and append
                        self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_REPLACED)
                        self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_REPLACED)
                        self.cmdNode.generateExitCmd(parentCommandTmp, config)
            else:
                if factsCmdNode.wantOnly:
                    nodeTmp = factsCmdNode.find(key)
                    parentCommandTmp = list()
                    if parentCommand:
                        parentCommandTmp.extend(parentCommand)
                    modeCommand = self.generateModeCommand(item, key, parentCommand, config)
                    # Skip processing this entry if modeCommand is not formed
                    if not modeCommand:
                        return

                    parentCommandTmp.append(modeCommand)
                    # Call replace for children
                    self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_REPLACED)
                    # Remove haveOnly config
                    factsTmp = Facts(None, None, factsCmdNode.haveOnly, None)
                    self.generateCommandForChildren(factsCmdNode, factsTmp, parentCommandTmp, config, Constant.STATE_DELETED)
                    # Call replace for submodes
                    self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_REPLACED)
        #    1.1 Locate facts node with ansibleName
        #    1.2 If above facts node is list,
        #    1.3 If subcommands are not present, mode delete case
        #      1.3.1 Call generateDeleteCommands() for cmdNode with old config
        #      1.3.2 Call generateMergeCommands() for cmdNode with new config
        #      1.3.2 Continue to process next item
        #    1.4 If subcommands are present, mode replace case
        #      1.4.1 Call generateMergeCommands() for cmdNode with old config
        #      1.4.2 Iterate all subcommands
        #        1.4.2.1 Call generateReplaceCommands for each list item
        #      1.4.3 Iterate all submodes
        #        1.4.3.1 Call generateReplaceCommands for each list item
        # 2. If cmdNode is not present,
        else:
            self.generateCommandForChildren(parentFacts, currentFacts, parentCommand, config, Constant.STATE_REPLACED)
        #    2.1 Iterate all children, for each children
        #    2.2 Locate the facts node
        #    2.3 Call generateReplaceCommands() with above facts node

    def generateOverriddenCommands(self, parentFacts, currentFacts,
                              parentCommand, config):
        """
        @brief Generate config from the facts (state : overridden)
               for ModeNode class

        @param config (NetworkConfig): Placeholder to append config
        @param parentFacts (dict): Has parentFacts node including
                                   all want-only, match, diff & have-only nodes
        @param parentCommand (list): List of commands from parent node
        @param currentFacts (dict): Facts to be converted as config
                             want-only, match, diff, have-only config are included

        @returns None
        """
        # TODO: Revisit the logic of checking subcommands are present or not
        #       Instead, facts node to be checked against subcommands
        #       Logic to separate old and new config from facts to be added
        # 1. If cmdNode is present
        if self.cmdNode:
            modeCommand = None
            factsCmdNode = currentFacts.find(self.cmdNode.ansibleName)
            # Return when factsCmdNode is empty
            if not factsCmdNode: return
            visitedKeys = list()
            if isinstance(self.cmdNode, ListNode):
                # 1. Iterate all keys in want-only facts, for each item
                if factsCmdNode.wantOnly:
                    for key, item in factsCmdNode.wantOnly.items():
                        diffNode = None
                        haveOnlyNode = None
                        nodeTmp = factsCmdNode.find(key)
                        parentCommandTmp = list()
                        if parentCommand:
                            parentCommandTmp.extend(parentCommand)
                        modeCommand = self.generateModeCommand(item, key, parentCommand, config)
                        # Skip processing this entry if modeCommand is not formed
                        if not modeCommand:
                            continue
                        parentCommandTmp.append(modeCommand)
                        # Generate command parts for children and append
                        self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
                        self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
                        # Get diff node matching the key of current item
                        if factsCmdNode.diff:
                            diffNode = factsCmdNode.diff.pop(key, None)
                        if diffNode:
                            self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
                            self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
                            visitedKeys.append(key)
                        # Get haveOnly node matching the key of current item
                        if factsCmdNode.haveOnly:
                            haveOnlyNode = factsCmdNode.haveOnly.pop(key, None)
                        if haveOnlyNode:
                            nodeTmp = Facts(None, None, None, haveOnlyNode)
                            self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
                            self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
                            visitedKeys.append(key)
                        self.cmdNode.generateExitCmd(parentCommandTmp, config)

                # 1. Iterate all keys in diff facts, for each item
                #    skip the key if present in visitedKeys
                if factsCmdNode.diff:
                    for key, item in factsCmdNode.diff.items():
                        haveOnlyNode = None
                        if key in visitedKeys: continue
                        nodeTmp = factsCmdNode.find(key)
                        parentCommandTmp = list()
                        if parentCommand:
                            parentCommandTmp.extend(parentCommand)
                        modeCommand = self.generateModeCommand(item, key, parentCommand, config)
                        # Skip processing this entry if modeCommand is not formed
                        if not modeCommand:
                            continue
                        parentCommandTmp.append(modeCommand)
                        # Generate command parts for children and append
                        self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
                        self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
                        visitedKeys.append(key)
                        # Get haveOnly node matching the key of current item
                        if factsCmdNode.haveOnly:
                            haveOnlyNode = factsCmdNode.haveOnly.pop(key, None)
                        if haveOnlyNode:
                            nodeTmp = Facts(None, None, None, haveOnlyNode)
                            self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
                            self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
                            visitedKeys.append(key)
                        self.cmdNode.generateExitCmd(parentCommandTmp, config)

                # Remove unwanted keys from haveOnly
                if factsCmdNode.haveOnly:
                    for key, item in factsCmdNode.haveOnly.items():
                        if key in visitedKeys: continue
                        parentCommandTmp = list()
                        if parentCommand:
                            parentCommandTmp.extend(parentCommand)
                        modeCommand = self.generateModeDeleteCommand(item, key, parentCommand, config)
                        parentCommandTmp.append(modeCommand)
                        self.cmdNode.generateExitCmd(parentCommandTmp, config)
            else:
                if factsCmdNode.wantOnly:
                    nodeTmp = factsCmdNode.find(key)
                    parentCommandTmp = list()
                    if parentCommand:
                        parentCommandTmp.extend(parentCommand)
                    modeCommand = self.generateModeCommand(item, key, parentCommand, config)
                    # Skip processing this entry if modeCommand is not formed
                    if not modeCommand:
                        return

                    parentCommandTmp.append(modeCommand)
                    # Call replace for children
                    self.generateCommandForChildren(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
                    # Call overridden for submodes
                    self.generateCommandForSubmode(factsCmdNode, nodeTmp, parentCommandTmp, config, Constant.STATE_OVERRIDDEN)
        #    1.1 Locate facts node with ansibleName
        #    1.2 If above facts node is list,
        #    1.3 If subcommands are not present, mode delete case
        #      1.3.1 Call generateDeleteCommands() for cmdNode with old config
        #      1.3.2 Call generateMergeCommands() for cmdNode with new config
        #      1.3.2 Continue to process next item
        #    1.4 If subcommands are present, mode replace case
        #      1.4.1 Call generateMergeCommands() for cmdNode with old config
        #      1.4.2 Iterate all subcommands
        #        1.4.2.1 Call generateReplaceCommands for each list item
        #      1.4.3 Iterate all submodes
        #        1.4.3.1 Call generateReplaceCommands for each list item
        # 2. If cmdNode is not present,
        else:
            self.generateCommandForChildren(parentFacts, currentFacts, parentCommand, config, Constant.STATE_OVERRIDDEN)
        #    2.1 Iterate all children, for each children
        #    2.2 Locate the facts node
        #    2.3 Call generateReplaceCommands() with above facts node

# Root node
class RootNode(Node):

    # Methods
    def __init__(self):
        super().__init__(isRoot=True)
        # Members
        self._listCache = list()
        # Use super().children as modes

    @property
    def listCache(self):
        return self._listCache

    @listCache.setter
    def listCache(self, value):
        self._listCache = value

    def dump(self):
        """
        @brief Print members of RootNode class
        """
        # log(f"RootNode")
        log_vars(listCache=self.listCache)
        self.dumpChildren()

    def buildTree(self, modes):
        """
        @brief Build tree from ref line for RootNode class

        @param modes (dict): Dict contains all modes of this resource module
        @param listCache (dict): Placeholder to update all list nodes
                                 required for compress & expand facts

        @returns None
        """
        # Format of reference line with modes
        # <mode>:
        #   <command, subcommands & submodes>
        # <mode>:
        #   ...
        # <mode>:
        #   ...
        # 1. Iterate over all modes
        for key, value in modes.items():
            # 1.1. Create object of ModeNode
            obj = ModeNode(name=key, parent=self)
            # 1.2. Add modeObj into children
            self.addChild(key, obj)
            # 1.3. Invoke mode buildTree with mode value
            obj.buildTree(value, self.listCache)
        log_vars(listCache=self.listCache)

    def buildCmdsToSearch(self):
        """
        @brief Build commands to search for while generating facts
               for RootNode class

        @param None

        @returns None
        """
        # 1. Iterate all modes & call buildCmdsToSearch for each node
        for key, mode in self.children.items():
            mode.buildCmdsToSearch()

    def generateFacts(self, config, facts):
        """
        @brief Generate facts from the config for RootNode class

        @param config (NetworkConfig): Configurations to be converted as facts
        @param facts (dict): Placeholder to update the facts

        @returns None
        """
        # 1. Iterate all modes & call generateFacts() for each mode,
        #    carry the same cfg & facts
        # log_vars(config=config)
        for key, mode in self.children.items():
            mode.generateFacts(config, facts) 

    def generateMergeCommands(self, config, facts):
        """
        @brief Generate config from the facts (state : merged)
               for RootNode class
               Merge = New in want + Update of Diff nodes
                       with values in want

        @param config (NetworkConfig): Placeholder to append config
        @param facts (dict): Facts to be converted as config
                             want-only, match, diff, have-only config
                             are included

        @returns None
        """
        # 1. Iterate all modes
        for key, mode in self.children.items():
            log(f"Processing {mode.name}")
        # 2. Invoke generateMergeCommands() for each mode,
        #    with the same cfg & facts
            mode.generateMergeCommands(None, facts, None, config)

    def generateDeleteForChildren(self, parentFacts, currentFacts,
                              parentCommand, config, deleteAll):
        # 6. For each children in item,
        for key, mode in self.children.items():
            log(f"Processing {mode.name}")
        #    6.1 Locate respective facts node
            if deleteAll:
                mode.generateDeleteAllCommands(parentFacts, currentFacts, parentCommand, config)
            else:
                mode.generateDeleteCommands(parentFacts, currentFacts, parentCommand, config)
        #    6.2 Append cliName and ansibleValue to temp command string parts

    def generateDeleteCommands(self, config, facts):
        """
        @brief Generate config from the facts (state : deleted)
               for RootNode class
               Delete : Negate of matching nodes
                        If want-only, match & diff are empty,
                        it is delete all case

        @param config (NetworkConfig): Placeholder to append config
        @param facts (dict): Facts to be converted as config
                             want-only, match, diff, have-only config are included

        @returns None
        """
        # 1. If want is empty, deleteAll case
        #    Call generateDeleteAllCommands with have-only nodes
        if facts.wantOnly is None and facts.diff is None and \
           facts.match is None and facts.haveOnly is not None:
            self.generateDeleteForChildren(None, facts, None, config, True)
            return
        # 2. Locate the match nodes
        #    2.1 Iterate all modes
        #    2.2 Invoke generateDeleteCommands() for each mode, carry the same cfg & facts
        self.generateDeleteForChildren(None, facts, None, config, False)

    def generateReplaceCommands(self, config, facts):
        """
        @brief Generate config from the facts (state : replaced)
               for RootNode class
               Replace: Merge of want-only & diff and
                        Delete of haveOnly for merged config

        @param config (NetworkConfig): Placeholder to append config
        @param facts (dict): Facts to be converted as config
                             want-only, match, diff, have-only config are included

        @returns None
        """
        # 1. Return when base is empty
        if facts.wantOnly is None and facts.diff is None and \
           facts.match is None and facts.haveOnly is not None:
            # TODO: Throw error
            log(f"No config items in play")
            return

        #    2.1 Iterate all modes
        for key, mode in self.children.items():
            log(f"Processing {mode.name}")
        #    2.2 Invoke generateReplaceCommands() for each mode,
        #        with the same cfg & facts
            mode.generateReplaceCommands(None, facts, None, config)

    def generateOverriddenCommands(self, config, facts):
        """
        @brief Generate config from the facts (state : replaced)
               for RootNode class
               Overridden: Replace operation + 
                           Remove all other entries from haveOnly
                           except replaced config items

        @param config (NetworkConfig): Placeholder to append config
        @param facts (dict): Facts to be converted as config
                             want-only, match, diff, have-only config are included

        @returns None
        """
        # 1. Return when base is empty
        if facts.wantOnly is None and facts.diff is None and \
           facts.match is None and facts.haveOnly is not None:
            # TODO: Throw error
            log(f"No config items in play")
            return

        #    2.1 Iterate all modes
        for key, mode in self.children.items():
            log(f"Processing {mode.name}")
        #    2.2 Invoke generateOverriddenCommands() for each mode,
        #        with the same cfg & facts
            mode.generateOverriddenCommands(None, facts, None, config)

    def buildConfig(self, want, have, state):
        """
        Build configurations from facts

        :param want: The configuration from play
        :param have: The configuration in managed node
        :param state: The state from playbook

        :returns config (list): List of generated config commands
        """
        commands = list()
        config = SonicNetworkConfig()

        # 1. Expand want
        # prettyJson = json.dumps(want, indent=4)
        # log(f"want (before expand)")
        # log(f"{prettyJson}")
        expandFacts(want, self.listCache)
        # prettyJson = json.dumps(want, indent=4)
        # log(f"want (after expand)")
        # log(f"{prettyJson}")

        # 2. Expand have
        # prettyJson = json.dumps(have, indent=4)
        # log(f"have (before expand)")
        # log(f"{prettyJson}")
        expandFacts(have, self.listCache)
        # prettyJson = json.dumps(have, indent=4)
        # log(f"have (after expand)")
        # log(f"{prettyJson}")

        # 3. Compare expanded want & have
        compareObj = CompareDict(want, have)
        compareObj.compare()
        compareObj.dump()
        # result = compareObj.compareNew()
        # prettyJson = json.dumps(result, indent=4)
        # log(f"result")
        # log(f"{prettyJson}")

        # Generate commands
        facts = Facts(compareObj=compareObj)
        # 5. Generate commands
        if state == Constant.STATE_MERGED:
            self.generateMergeCommands(config, facts)
        elif state == Constant.STATE_DELETED:
            self.generateDeleteCommands(config, facts)
        elif state == Constant.STATE_REPLACED:
            self.generateReplaceCommands(config, facts)
        elif state == Constant.STATE_OVERRIDDEN:
            self.generateOverriddenCommands(config, facts)
        else:
            # TODO: Throw error
            log(f"Unknown state {state}")

        # Convert config to commands
        log_vars(config=str(config))
        for item in config.items:
            commands.append(item.text)

        # 4. Compress the dicts in comparision result
        compressFacts(want, self.listCache)
        # prettyJson = json.dumps(want, indent=4)
        # log(f"want (after compress)")
        # log(f"{prettyJson}")

        compressFacts(have, self.listCache)
        # prettyJson = json.dumps(have, indent=4)
        # log(f"have (after compress)")
        # log(f"{prettyJson}")

        # compressFacts(compareObj.baseOnly, self.listCache)
        # prettyJson = json.dumps(compareObj.baseOnly, indent=4)
        # log(f"compareObj.baseOnly (after compress)")
        # log(f"{prettyJson}")

        # compressFacts(compareObj.match, self.listCache)
        # prettyJson = json.dumps(compareObj.match, indent=4)
        # log(f"compareObj.match (after compress)")
        # log(f"{prettyJson}")

        # compressFacts(compareObj.diff, self.listCache)
        # prettyJson = json.dumps(compareObj.diff, indent=4)
        # log(f"compareObj.diff (after compress)")
        # log(f"{prettyJson}")

        # compressFacts(compareObj.comparableOnly, self.listCache)
        # prettyJson = json.dumps(compareObj.comparableOnly, indent=4)
        # log(f"compareObj.comparableOnly (after compress)")
        # log(f"{prettyJson}")

        return commands

