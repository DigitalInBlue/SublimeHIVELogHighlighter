#!/usr/bin/python3

## An iterator for an xml document.
#  @package Module_XMLTagIterator
#  @author Vincent Yahna
#
#  An XMLTagIterator class
#  that iterates through
#  regions in a sublime view.

import sublime

## An iterator for tag regions in a view
#  that contains xml data.
#  Should not be used while
#  there is concurrent editing of the view.
class XMLTagIterator():

    ## constructor
    #  @param view - a Sublime view object
    #  @param location - an integer index into the view.
    #  If location is not in a tag, the closest tag to the
    #  right of that location is used
    def __init__(self, view, location):
        ## the sublime view the tags belong to
        self.view = view
        
        #it is assumed that find_all returns the regions in order
        #(but this is not directly stated by documentation, so sorting
        #may be necessary in the future if specifications change)

        #get comment tags and tags and make re not greedy with ?
        tagsRE = "<!--[\s\S]*?-->|<[\s\S]*?>" 
        ## a list of regions that contain tags
        self.tagRegions = self.view.find_all(tagsRE)
        ## an integer index into tagRegions
        self.index = len(self.tagRegions) -1

        while(self.index >= 0):
            #get the tag that location is inside
            if(self.tagRegions[self.index].contains(location) ):
                break
            #or find the tag that location is in front of
            elif(self.tagRegions[self.index].end() <= location):
                #set to the tag after the current location
                self.index +=1
                break
            self.index -=1

        #if self.index is -1, no tag was found before location
        if(self.index == -1):
            self.index = 0

    ## Changes the iterator to another location using the same sublime View.
    #  This is less computationally expensive than creating a new iterator 
    #  since tag regions do not need to be found again.
    #  @param location - an integer index into the view.
    #  If location is not in a tag, the closest tag to the
    #  right of that location is used
    def reinitialize(self,  location):
        
        self.index = len(self.tagRegions) -1

        while(self.index >= 0):
            #get the tag location is inside
            if(self.tagRegions[self.index].contains(location) ):
                break
            #or find the tag that location is in front of
            elif(self.tagRegions[self.index].end() <= location):
                #set to the tag after the current location
                self.index +=1
                break
            self.index -=1

        #if self.index is -1, no tag was found before location
        if(self.index == -1):
            self.index = 0

    ## Test for determining if the current
    #  tag is a comment tag.
    #  @returns True or False
    def isCommentTag(self):
        region = self.currentTag()
        if(region is None):
            return False #out of bounds
        else:
            return self.view.score_selector(region.begin(), "comment.block.xml")


    ## Test for determining if the current
    #  tag is a PI tag.
    #  @returns True or False
    def isPITag(self):
        region = self.currentTag()
        if(region is None):
            return False #out of bounds
        else:
            return self.view.score_selector(region.begin(), "meta.tag.preprocessor.xml")


    ## Get the current tag
    #  @returns a region or None
    def currentTag(self):
        if(self.index >= 0 and self.index < len(self.tagRegions)):
            return self.tagRegions[self.index]
        else:
            return None

    ## Decrement the iterator and get the tag at that position.
    #  @param skipPI - optional boolean indicating to skip processing instruction tags
    #  @param skipComment - optional boolean indicating to skip comment tags
    #  @returns a region or None
    def previousTag(self, skipPI=False, skipComment=False):
        self.index -= 1
        while((self.isPITag() and skipPI) or (self.isCommentTag() and skipComment)):
            self.index-=1

        if(self.index >= 0 and self.index < len(self.tagRegions)):
            return self.tagRegions[self.index]
        else:
            return None

    ## Increment the iterator and get the tag at that position.
    #  @param skipPI - optional boolean indicating to skip processing instruction tags
    #  @param skipComment - optional boolean indicating to skip comment tags
    #  @returns a region or None
    def nextTag(self, skipPI=False, skipComment=False):
        self.index += 1

        while((self.isPITag() and skipPI) or (self.isCommentTag() and skipComment)):
            self.index +=1

        if(self.index >= 0 and self.index < len(self.tagRegions)):
            return self.tagRegions[self.index]
        else:
            return None

    ## Decrement the iterator until the parent of the current
    #  tag is found and return that tag.
    #  The parent of an ending tag is its opening tag.
    #  @returns a region or None
    def getParent(self):
        parentNotFound = True #found when no closing tags are left in stack
        stack = [] #keep track of closing tags

        #find the parent tag
        while(parentNotFound):
            tag = self.previousTag(skipPI=True, skipComment=True)

            if(tag is None):
                return None #no tags left to check

            currentLine = self.view.substr(tag)
            tokens = currentLine.replace('=', ' = ').replace('<', ' < ').replace('\"', ' \" ').replace('/', ' / ').replace('>', ' > ').split()

            if(tokens[-2] == '/'):
                pass #ignore stand alone tags
            elif(tokens[1] == '/'): #ending tag found
                stack.append(tokens[2])
                parentNotFound = len(stack) > 0 #keep iterating while the stack isn't empty
            elif(len(stack) >= 1 and stack[-1] == tokens[1]):
                stack.pop()
            else:
                parentNotFound = len(stack) > 0 #keep iterating while the stack isn't empty

        return self.tagRegions[self.index]

    ## Increment iterator until the closing tag for
    #  the current tag is found and return that tag.
    #  Stand-alone, ending, comment, and processing
    #  instruction tags do not have ending tags so
    #  if this method is called for one, the same tag
    #  is returned and the iterator is not incremented.
    #  @returns a region or None
    def getClosingTag(self):
        #check if current tag is comment or PI
        if(self.isPITag() or self.isCommentTag()):
            return self.currentTag()
        #check if the current tag is an ending tag or standalone tag
        tag = self.currentTag()
        if(tag is not None):
            tagText = self.view.substr(tag)
            tokens = tagText.replace('=', ' = ').replace('<', ' < ').replace('\"', ' \" ').replace('/', ' / ').replace('>', ' > ').split()
            if(tokens[1] == '/' or tokens[-2] == '/'):
                return tag


        endNotFound = True #found when no opening tags are left in stack
        stack = [] #keep track of opening tags

        #find the ending tag
        while(endNotFound):
            tag = self.nextTag(skipPI=True, skipComment=True)

            if(tag is None):
                return None #no tags left to check

            currentLine = self.view.substr(tag)
            tokens = currentLine.replace('=', ' = ').replace('<', ' < ').replace('\"', ' \" ').replace('/', ' / ').replace('>', ' > ').split()

            if(tokens[-2] == '/'):
                pass #ignore stand alone tags
            elif(len(stack) > 0 and tokens[1] == '/' and stack[-1]==tokens[2]): #ending tag found
                stack.pop()
            elif(tokens[1] == '/'): #found end tag and nothing is on stack
                endNotFound = len(stack) > 0
            else:#normal tag, append element name
                stack.append(tokens[1])


        return self.tagRegions[self.index]