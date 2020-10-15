# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_inner
from collective.contentrules.mailfromfield import logger
from collective.contentrules.mailfromfield.actions.mail import IMailFromFieldAction
from collective.contentrules.mailfromfield.actions.mail import MailActionExecutor as BaseExecutor
from DateTime import DateTime
from plone.contentrules.rule.interfaces import IExecutable
# from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from redturtle.prenotazioni.content.prenotazione import Prenotazione
from six.moves import filter
from zope.component import adapter
from zope.component._declaration import adapts
from zope.interface import implementer
from zope.interface import Interface
from zope.interface.declarations import implements

import six



@implementer(IExecutable)
@adapter(IPloneSiteRoot, IMailFromFieldAction, Interface)
class MailActionExecutor(BaseExecutor):
    """The executor for this action.
    """

    def get_mapping(self):
        '''Return a mapping that will replace markers in the template
        extended with the markers:
         - ${gate}
         - ${date}
         - ${subject}
         - ${time}
         - ${type}
        '''
        mapping = super(MailActionExecutor, self).get_mapping()
        event_obj = self.event.object

        if not isinstance(event_obj, Prenotazione):
            return mapping

        mapping['gate'] = event_obj.getGate() or ''
        mapping['subject'] = event_obj.Description() or ''
        mapping['type'] = event_obj.getTipologia_prenotazione() or ''

        event_obj_date = event_obj.Date()
        if not event_obj_date:
            return mapping

        date = DateTime(event_obj.Date())
        plone = self.context.restrictedTraverse('@@plone')
        mapping.update({"date": plone.toLocalizedTime(date),
                        "time": plone.toLocalizedTime(date, time_only=True),
                        })
        return mapping

    def get_target_obj(self):
        '''Get's the target object, i.e. the object that will provide the field
        with the email address
        '''
        target = self.element.target
        if target == 'object':
            obj = self.context
        elif target == 'parent':
            obj = self.event.object.aq_parent
            # NEEDED JUST FOR PRENOTAZIONI...
            return obj
        elif target == 'target':
            obj = self.event.object
        else:
            raise ValueError(target)
        return aq_base(aq_inner(obj))


    def get_recipients(self):
        '''
        The recipients of this mail
        '''
        # Try to load data from the target object
        fieldName = str(self.element.fieldName)
        obj = self.get_target_obj()

        # 1: object attribute
        try:
            # BBB don't have time to investigate difference between original __getattribute__
            # and this getattr... _getattribute__ remove the possibility to use objects chain
            attr = getattr(obj, fieldName)
            # 3: object method
            if hasattr(attr, '__call__'):
                recipients = attr()
                logger.debug('getting e-mail from %s method' % fieldName)
            else:
                recipients = attr
                logger.debug('getting e-mail from %s attribute' % fieldName)
        except AttributeError:
            # 2: try with AT field
            # if IBaseContent.providedBy(obj):
            #     field = obj.getField(fieldName)
            #     if field:
            #         recipients = field.get(obj)
            #     else:
            #         recipients = False
            # else:
            recipients = False
            if not recipients:
                recipients = obj.getProperty(fieldName, [])
                if recipients:
                    logger.debug('getting e-mail from %s CMF property'
                                 % fieldName)
            else:
                logger.debug('getting e-mail from %s AT field' % fieldName)

        # now transform recipients in a iterator, if needed
        if type(recipients) == str or type(recipients) == six.text_type:
            recipients = [str(recipients), ]
        return list(filter(bool, recipients))

