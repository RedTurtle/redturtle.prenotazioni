import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import WidgetContext from '../utils/widgetContext';
import SelectField from './SelectField';
import './DaysTableField.less';

const DaysTableField = ({ value, row }) => {
  const { getTranslationFor, updateField } = useContext(WidgetContext);

  const onUpdateSelect = ({ row: selectRow, id, value: selectValue }) => {
    let newValue = [...value.week_table];
    newValue[selectRow][id] = selectValue;
    console.log('newValue: ', newValue);
    updateField({ row, id: 'week_table', value: newValue });
  };
  return (
    <div className="days-table-wrapper">
      <table>
        <thead>
          <tr>
            <th>
              <span>{getTranslationFor('day_label')}</span>
            </th>
            <th>
              <span>{getTranslationFor('morning_start_label')}</span>
            </th>

            <th>
              <span>{getTranslationFor('morning_end_label')}</span>
            </th>
            <th>
              <span>{getTranslationFor('afternoon_start_label')}</span>
            </th>
            <th>
              <span>{getTranslationFor('afternoon_end_label')}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {value.week_table.map((day, dayIdx) => (
            <tr key={dayIdx}>
              <td>{day.day}</td>
              <td>
                <SelectField
                  value={day.morning_start}
                  id="morning_start"
                  row={dayIdx}
                  vocId="timetable"
                  customUpdateField={onUpdateSelect}
                  placeholder={getTranslationFor('morning_start_label')}
                />
              </td>
              <td>
                <SelectField
                  value={day.morning_end}
                  id="morning_end"
                  row={dayIdx}
                  vocId="timetable"
                  customUpdateField={onUpdateSelect}
                  placeholder={getTranslationFor('morning_end_label')}
                />
              </td>
              <td>
                <SelectField
                  value={day.afternoon_start}
                  id="afternoon_start"
                  row={dayIdx}
                  vocId="timetable"
                  customUpdateField={onUpdateSelect}
                  placeholder={getTranslationFor('afternoon_start_label')}
                />
              </td>
              <td>
                <SelectField
                  value={day.afternoon_end}
                  id="afternoon_end"
                  row={dayIdx}
                  vocId="timetable"
                  customUpdateField={onUpdateSelect}
                  placeholder={getTranslationFor('afternoon_end_label')}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

DaysTableField.propTypes = {
  value: PropTypes.object,
  row: PropTypes.number,
};

export default DaysTableField;
