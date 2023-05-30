import React, { useContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import WidgetContext from '../utils/widgetContext';

const TextLineField = ({ value, id, row, type = 'text' }) => {
  const { updateField } = useContext(WidgetContext);
  const [data, setData] = useState({ text: '', timeout: 0 });

  const updateText = targetValue => {
    if (data.timeout) {
      clearInterval(data.timeout);
    }
    const timeout = setTimeout(() => {
      updateField({ row, id, value: targetValue });
    }, 1000);
    setData({ text: targetValue, timeout });
  };

  useEffect(() => {
    setData({ text: value, timeout: 0 });
  }, [value]);

  return (
    <input
      type={type}
      value={data.text}
      onChange={e => updateText(e.target.value)}
    />
  );
};
TextLineField.propTypes = {
  value: PropTypes.string,
  id: PropTypes.string,
  row: PropTypes.number,
  type: PropTypes.string,
};

export default TextLineField;
