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

  return (
    <tr key={row}>
      <td>
        <SelectField
          value={value.day}
          id="day"
          vocId="weekDays"
          key={'day' + row}
          row={row}
          customUpdateField={onUpdateSelect}
          placeholder={getTranslationFor('day_label')}
        />
      </td>
      <td>
        <SelectField
          value={value.pause_start}
          id="pause_start"
          vocId="timetable"
          key={'pause_start' + row}
          row={row}
          customUpdateField={onUpdateSelect}
          placeholder={getTranslationFor('pause_start_label')}
        />
      </td>
      <td>
        <SelectField
          value={value.pause_end}
          id="pause_end"
          vocId="timetable"
          key={'pause_end' + row}
          row={row}
          customUpdateField={onUpdateSelect}
          placeholder={getTranslationFor('pause_end_label')}
        />
      </td>
      <td className="actions">
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
    <div className="pause-table-wrapper">
      <div>
        <strong>{getTranslationFor('Pause table')}</strong>
      </div>
      <div>
        {pause_table.length > 0 && (
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
        )}

        <button className="context" type="button" onClick={onAddRow}>
          <FontAwesomeIcon icon={faPlus} /> {getTranslationFor('Add')}
        </button>
      </div>
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
