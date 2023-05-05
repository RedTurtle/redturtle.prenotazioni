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
          value={value.fromDay}
          id="fromDay"
          row={row}
          vocId="days"
        />
      </div>
      <div className="column block">
        <label>{getTranslationFor('month_label')}</label>
        <SelectField
          value={value.fromMonth}
          id="fromMonth"
          row={row}
          vocId="months"
        />
      </div>
      <strong>{getTranslationFor('to_label')}</strong>
      <div className="column block">
        <label>{getTranslationFor('day_label')}</label>
        <SelectField value={value.toDay} id="toDay" row={row} vocId="days" />
      </div>
      <div className="column block">
        <label>{getTranslationFor('month_label')}</label>
        <SelectField
          value={value.toMonth}
          id="toMonth"
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
