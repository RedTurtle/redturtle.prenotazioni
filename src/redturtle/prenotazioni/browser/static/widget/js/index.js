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
      timetable: `${baseUrl}/@vocabularies/redturtle.prenotazioni.VocOreInizio?b_size=1000`,
      months: `${baseUrl}/@vocabularies/redturtle.prenotazioni.VocMonths?b_size=1000`,
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
