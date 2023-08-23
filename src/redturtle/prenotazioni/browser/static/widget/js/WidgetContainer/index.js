import React, { Component } from 'react';
import PropTypes from 'prop-types';
import WidgetDataContainer from '../WidgetDataContainer';
import axios from 'axios';
import WidgetContext from '../utils/widgetContext';
import { getTranslationCatalog } from '../utils/i18n';
import arrayMove from 'array-move';

class WidgetContainer extends Component {
  constructor(props) {
    super(props);
    const fieldValue = document.getElementById(props.fieldId).value;
    const value = fieldValue.length > 0 ? JSON.parse(fieldValue) : [];

    this.getTranslationFor = msgid => {
      const { translations } = this.state;
      return translations[msgid] || msgid;
    };

    const updateWidgetField = value => {
      console.log('VALORE AGGIORNATO: ', value);
      document.getElementById(this.props.fieldId).value = JSON.stringify(value);
    };

    this.addRow = () => {
      let newValue = this.state.value.map(entry => entry);
      newValue.push({
        from_day: '',
        from_month: '',
        to_day: '',
        to_month: '',
        week_table: [
          {
            day: 'Lunedì',
            morning_start: '',
            morning_end: '',
            afternoon_start: '',
            afternoon_end: '',
          },
          {
            day: 'Martedì',
            morning_start: '',
            morning_end: '',
            afternoon_start: '',
            afternoon_end: '',
          },
          {
            day: 'Mercoledì',
            morning_start: '',
            morning_end: '',
            afternoon_start: '',
            afternoon_end: '',
          },
          {
            day: 'Giovedì',
            morning_start: '',
            morning_end: '',
            afternoon_start: '',
            afternoon_end: '',
          },
          {
            day: 'Venerdì',
            morning_start: '',
            morning_end: '',
            afternoon_start: '',
            afternoon_end: '',
          },
          {
            day: 'Sabato',
            morning_start: '',
            morning_end: '',
            afternoon_start: '',
            afternoon_end: '',
          },
          {
            day: 'Domenica',
            morning_start: '',
            morning_end: '',
            afternoon_start: '',
            afternoon_end: '',
          },
        ],
        gates: [],
        pause_table: [],
      });
      this.setState({
        ...this.state,
        value: newValue,
      });
      updateWidgetField(newValue);
    };

    this.removeRow = row => {
      let newValue = this.state.value.filter((entry, idx) => idx !== row);
      this.setState({
        ...this.state,
        value: newValue,
      });
      updateWidgetField(newValue);
    };

    this.moveRow = ({ from, to }) => {
      const newValue = arrayMove(this.state.value, from, to);
      this.setState({
        ...this.state,
        value: newValue,
      });
      updateWidgetField(newValue);
    };

    this.updateField = ({ id, value, row }) => {
      let updatedValue = this.state.value;
      updatedValue[row][id] = value;
      this.setState({
        ...this.state,
        value: updatedValue,
      });
      updateWidgetField(updatedValue);
    };

    this.state = {
      value,
      vocabularies: {
        days: {
          items: Array.from({ length: 31 }, (value, index) => {
            const key = index + 1;
            return { token: key.toString(), title: key.toString() };
          }),
        },
        weekDays: {
          items: [
            { token: '0', title: 'Monday' },
            { token: '1', title: 'Tuesday' },
            { token: '2', title: 'Wednesday' },
            { token: '3', title: 'Thursday' },
            { token: '4', title: 'Friday' },
            { token: '5', title: 'Saturday' },
            { token: '6', title: 'Sunday' },
          ],
        },
      },
      translations: {},
      addRow: this.addRow,
      removeRow: this.removeRow,
      moveRow: this.moveRow,
      updateField: this.updateField,
      getTranslationFor: this.getTranslationFor,
    };
    // fetch translations
    getTranslationCatalog().then(data => {
      this.setState({ ...this.state, translations: data });
    });
    // fetch vocabularies
    const { schema } = props;
    Promise.all(
      Object.keys(schema.vocabularies).map(vocId => {
        return axios({
          method: 'GET',
          url: schema.vocabularies[vocId],
          headers: { Accept: 'application/json' },
        }).then(data => {
          this.setState({
            ...this.state,
            vocabularies: {
              ...this.state.vocabularies,
              [vocId]: data.data,
            },
          });
        });
      }),
    );
  }
  render() {
    return (
      <WidgetContext.Provider
        value={{ ...this.state, schema: this.props.schema }}
      >
        <WidgetDataContainer></WidgetDataContainer>
      </WidgetContext.Provider>
    );
  }
}
WidgetContainer.propTypes = {
  baseUrl: PropTypes.string,
  fieldId: PropTypes.string,
  schema: PropTypes.object,
};

export default WidgetContainer;
