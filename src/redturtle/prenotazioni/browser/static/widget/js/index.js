import React from 'react';
import ReactDOM from 'react-dom';
import WidgetContainer from './WidgetContainer';

document.addEventListener('DOMContentLoaded', function() {
  const widgets = document.getElementsByClassName(
    'week-table-overrides-widget',
  );
  const baseUrl = document.body.getAttribute('data-base-url');
  const schema = {
    vocabularies: {
      timetable:
        'http://localhost:8080/Plone/@vocabularies/redturtle.prenotazioni.VocOreInizio',
      months:
        'http://localhost:8080/Plone/@vocabularies/redturtle.prenotazioni.VocMonths',
    },
  };
  if (widgets.length) {
    Array.from(widgets).forEach(element => {
      const root = element.querySelector('.widget-wrapper');
      const field = element.querySelector('.widget-field');
      ReactDOM.render(
        <WidgetContainer
          baseUrl={baseUrl}
          fieldId={field.getAttribute('id')}
          schema={schema}
        />,
        root,
      );
    });
  }
});
