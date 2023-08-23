import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import WidgetContext from '../utils/widgetContext';
import SelectField from './SelectField';
import './IntervalSelectorField.less';

const IntervalSelectorField = ({ value, row }) => {
  const { getTranslationFor } = useContext(WidgetContext);

  return (
    <div className="period-selector-wrapper">
      <div className="period">
        <div className="column block label">
          <strong>{getTranslationFor('from_label')}</strong>
        </div>
        <div className="column block">
          <SelectField
            value={value.from_day}
            id="from_day"
            row={row}
            vocId="days"
            placeholder={getTranslationFor('day_label')}
          />
        </div>

        <div className="column block">
          <SelectField
            value={value.from_month}
            id="from_month"
            row={row}
            vocId="months"
            placeholder={getTranslationFor('month_label')}
          />
        </div>
      </div>
      <div className="period">
        <div className="column block label">
          <strong>{getTranslationFor('to_label')}</strong>
        </div>
        <div className="column block">
          <SelectField
            value={value.to_day}
            id="to_day"
            row={row}
            vocId="days"
            placeholder={getTranslationFor('day_label')}
          />
        </div>
        <div className="column block">
          <SelectField
            value={value.to_month}
            id="to_month"
            row={row}
            vocId="months"
            placeholder={getTranslationFor('month_label')}
          />
        </div>
      </div>
    </div>
  );
};

IntervalSelectorField.propTypes = {
  value: PropTypes.object,
  row: PropTypes.number,
};

export default IntervalSelectorField;
