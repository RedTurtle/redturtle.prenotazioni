import React, { useContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import WidgetContext from '../utils/widgetContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faTrash } from '@fortawesome/free-solid-svg-icons';

import './GatesField.less';

const LineField = ({ value, row, updateField }) => {
  const [data, setData] = useState({ text: '', timeout: 0 });

  const updateText = targetValue => {
    if (data.timeout) {
      clearInterval(data.timeout);
    }
    const timeout = setTimeout(() => {
      updateField({ row, id: 'gates', value: targetValue });
    }, 400);
    setData({ text: targetValue, timeout });
  };
  useEffect(() => {
    setData({ text: value, timeout: 0 });
  }, [value]);

  return (
    <input
      type="text"
      className="input-line"
      value={data.text}
      onChange={e => updateText(e.target.value)}
    />
  );
};

const GatesField = ({ value, row }) => {
  const { gates } = value;
  const { updateField, getTranslationFor } = useContext(WidgetContext);
  const onUpdateRow = data => {
    const newValue = gates.map((rowText, rowIdx) => {
      if (rowIdx === data.row) {
        return data.value;
      } else {
        return rowText;
      }
    });
    updateField({ row, id: 'gates', value: newValue });
  };

  const onAddRow = e => {
    e.preventDefault();
    let newValue = gates.map(text => text);
    newValue.push('');
    updateField({ row, id: 'gates', value: newValue });
  };
  const onDeleteRow = deletedRow => {
    let newValue = gates.filter((text, idx) => idx !== deletedRow);
    updateField({ row, id: 'gates', value: newValue });
  };

  return (
    <div className="gates-rows">
      <div>
        <strong>{getTranslationFor('gates_label')}</strong>
      </div>
      {gates.map((rowValue, idx) => (
        <div className="row" key={`gates-row-${idx}`}>
          <div className="column">
            <LineField row={idx} updateField={onUpdateRow} value={rowValue} />
          </div>
          <div className="column">
            <button
              className="destructive"
              type="button"
              onClick={e => {
                e.preventDefault();
                onDeleteRow(idx);
              }}
              title={getTranslationFor('Delete')}
            >
              <FontAwesomeIcon icon={faTrash} />
            </button>
          </div>
        </div>
      ))}
      <div>
        <button className="context" type="button" onClick={onAddRow}>
          <FontAwesomeIcon icon={faPlus} /> {getTranslationFor('Add')}
        </button>
      </div>
    </div>
  );
};

LineField.propTypes = {
  value: PropTypes.string,
  row: PropTypes.number,
  updateField: PropTypes.func,
};
GatesField.propTypes = {
  value: PropTypes.object,
  row: PropTypes.number,
};

export default GatesField;
