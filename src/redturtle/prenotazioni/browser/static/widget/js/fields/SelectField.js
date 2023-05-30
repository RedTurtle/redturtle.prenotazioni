import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Select from 'react-select';
import WidgetContext from '../utils/widgetContext';

// import './index.less';

const SelectField = ({ value, id, row, vocId, multi, customUpdateField }) => {
  const { vocabularies, updateField } = useContext(WidgetContext);
  const vocab = vocabularies[vocId];
  if (!vocab) {
    return '';
  }
  const options = vocab.items.map(item => {
    return { value: item.token, label: item.title };
  });
  const selectValue = options.filter(option => {
    if (Array.isArray(value)) {
      return value.includes(option.value);
    } else {
      return value === option.value;
    }
  });
  return (
    <Select
      isMulti={multi ? true : false}
      isClearable={true}
      defaultValue={selectValue}
      options={options}
      onChange={option => {
        let newValue = null;
        if (Array.isArray(value)) {
          newValue = option ? option.map(item => item.value) : [];
        } else {
          newValue = option ? option.value : '';
        }
        customUpdateField
          ? customUpdateField({ row, id, value: newValue })
          : updateField({ row, id, value: newValue });
      }}
    />
  );
};
SelectField.propTypes = {
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.array]),
  id: PropTypes.string,
  vocId: PropTypes.string,
  multi: PropTypes.bool,
  row: PropTypes.number,
  customUpdateField: PropTypes.func,
};

export default SelectField;
