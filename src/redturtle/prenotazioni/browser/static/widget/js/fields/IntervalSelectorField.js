import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import WidgetContext from '../utils/widgetContext';
import SelectField from './SelectField';
import './IntervalSelectorField.less';

const IntervalSelectorField = ({ value, row }) => {
  const { getTranslationFor } = useContext(WidgetContext);

  return (
    <div className="period-selector-wrapper">
      <strong>{getTranslationFor('from_label')}</strong>
      <div className="column block">
        <label>{getTranslationFor('day_label')}</label>
        <SelectField
          value={value.from_day}
          id="from_day"
          row={row}
          vocId="days"
        />
      </div>
      <div className="column block">
        <label>{getTranslationFor('month_label')}</label>
        <SelectField
          value={value.from_month}
          id="from_month"
          row={row}
          vocId="months"
        />
      </div>
      <strong>{getTranslationFor('to_label')}</strong>
      <div className="column block">
        <label>{getTranslationFor('day_label')}</label>
        <SelectField value={value.to_day} id="to_day" row={row} vocId="days" />
      </div>
      <div className="column block">
        <label>{getTranslationFor('month_label')}</label>
        <SelectField
          value={value.to_month}
          id="to_month"
          row={row}
          vocId="months"
        />
      </div>
    </div>
  );
};

IntervalSelectorField.propTypes = {
  value: PropTypes.object,
  row: PropTypes.number,
};

export default IntervalSelectorField;
