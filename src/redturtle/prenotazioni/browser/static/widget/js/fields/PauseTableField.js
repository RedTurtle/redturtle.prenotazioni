import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import WidgetContext from '../utils/widgetContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faTrash } from '@fortawesome/free-solid-svg-icons';
import SelectField from './SelectField';

import './PauseTableField.less';

const PauseRow = ({ value, row, updateField, onDeleteRow }) => {
  const { getTranslationFor } = useContext(WidgetContext);

  const onUpdateSelect = ({ id, value: selectValue }) => {
    let newValue = { ...value };
    newValue[id] = selectValue;
    updateField({ row, value: newValue });
  };
  console.log(value);
  return (
    <tr>
      <td>
        <SelectField
          value={value.day}
          id="day"
          row={row}
          vocId="weekDays"
          customUpdateField={onUpdateSelect}
        />
      </td>
      <td>
        <SelectField
          value={value.pause_start}
          id="pause_start"
          row={row}
          vocId="timetable"
          customUpdateField={onUpdateSelect}
        />
      </td>
      <td>
        <SelectField
          value={value.pause_end}
          id="pause_end"
          row={row}
          vocId="timetable"
          customUpdateField={onUpdateSelect}
        />
      </td>
      <td>
        <button
          className="destructive"
          type="button"
          onClick={e => {
            e.preventDefault();
            onDeleteRow(row);
          }}
          title={getTranslationFor('Delete')}
        >
          <FontAwesomeIcon icon={faTrash} />
        </button>
      </td>
    </tr>
  );
};

const PauseTableField = ({ value, row }) => {
  const { pause_table } = value;
  const { updateField, getTranslationFor } = useContext(WidgetContext);

  const onUpdateRow = data => {
    const newValue = pause_table.map((rowValue, rowIdx) =>
      rowIdx === data.row ? data.value : rowValue,
    );
    updateField({ row, id: 'pause_table', value: newValue });
  };

  const onAddRow = e => {
    e.preventDefault();
    let newValue = pause_table.map(value => value);
    newValue.push({ day: null, pause_start: null, pause_end: null });
    updateField({ row, id: 'pause_table', value: newValue });
  };
  const onDeleteRow = deletedRow => {
    let newValue = pause_table.filter((value, idx) => idx !== deletedRow);
    updateField({ row, id: 'pause_table', value: newValue });
  };

  return (
    <div className="array-rows">
      <strong>{getTranslationFor('pause_table_label')}</strong>
      <table>
        <thead>
          <tr>
            <th>
              <span>{getTranslationFor('day_label')}</span>
            </th>
            <th>
              <span>{getTranslationFor('pause_start_label')}</span>
            </th>

            <th>
              <span>{getTranslationFor('pause_end_label')}</span>
            </th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {pause_table.map((rowValue, idx) => (
            <PauseRow
              row={idx}
              key={`row-${idx}`}
              updateField={onUpdateRow}
              onDeleteRow={onDeleteRow}
              value={rowValue}
            ></PauseRow>
          ))}
        </tbody>
      </table>

      <button className="context" type="button" onClick={onAddRow}>
        <FontAwesomeIcon icon={faPlus} /> {getTranslationFor('Add')}
      </button>
    </div>
  );
};

PauseRow.propTypes = {
  value: PropTypes.object,
  row: PropTypes.number,
  updateField: PropTypes.func,
  onDeleteRow: PropTypes.func,
};
PauseTableField.propTypes = {
  value: PropTypes.object,
  row: PropTypes.number,
};

export default PauseTableField;
