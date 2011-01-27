# -*- coding: utf-8 -*-
from django.test import TestCase
from models import WikipediaElement

class WikipediaTestCase(TestCase):

    def test_import(self):
        '''Test of importing wikipedia page'''
        element1 = WikipediaElement.objects.update('ru', u'Беспечный ездок')

        self.assertEqual(WikipediaElement.objects.count(), 1)

        element2 = WikipediaElement.objects.all()[0]
        self.assertEqual(element1, element2)
        self.assertTrue(element2.content.find(u'художественный фильм') != -1)
        self.assertTrue(element2.content.find('<span lang="en" xml:lang="en">Easy Rider</span>') != -1)