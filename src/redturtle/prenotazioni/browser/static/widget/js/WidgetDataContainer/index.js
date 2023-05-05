import React, { useContext, useState } from 'react';
import PropTypes from 'prop-types';
import WidgetContext from '../utils/widgetContext';
import IntervalSelectorField from '../fields/IntervalSelectorField';
import DaysTableField from '../fields/DaysTableField';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faPlus,
  faTrash,
  faArrowUp,
  faArrowDown,
  faChevronDown,
  faChevronRight,
} from '@fortawesome/free-solid-svg-icons';

import './index.less';
import { Collapse } from 'react-collapse';

const WidgetDataContainer = () => {
  const { value, addRow, removeRow, moveRow, getTranslationFor } = useContext(
    WidgetContext,
  );

  const [expandedGroups, setExpandedGroups] = useState({});

  const toggleGroup = group => {
    setExpandedGroups({
      ...expandedGroups,
      [group]: !expandedGroups[group],
    });
  };

  const getLabel = entry => {
    let label = '';
    if (entry.fromDay.length && entry.fromMonth.length) {
      label += `${entry.fromDay}/${entry.fromMonth}`;
    }
    if (entry.toDay.length && entry.toMonth.length) {
      label += ` - ${entry.toDay}/${entry.toMonth}`;
    }
    return label;
  };

  return (
    <div className="data-wrapper">
      {value.map((entry, idx) => {
        const isOpen = expandedGroups[idx] === true;
        const expandCollapseLabel = isOpen ? 'Collapse' : 'Expand';
        const label = getLabel(entry);
        return (
          <div className="json-row" key={idx}>
            <div className="row-header">
              <button
                className="standalone"
                type="button"
                title={getTranslationFor(
                  expandCollapseLabel,
                  expandCollapseLabel,
                )}
                onClick={e => {
                  e.preventDefault();
                  toggleGroup(idx);
                }}
              >
                <FontAwesomeIcon
                  icon={isOpen ? faChevronDown : faChevronRight}
                />
              </button>
              <strong>
                {label ? label : `${getTranslationFor('Group')} ${idx + 1}`}
              </strong>
              <div className="actions">
                {idx + 1 !== value.length && (
                  <button
                    className="standalone"
                    type="button"
                    title={getTranslationFor('Move down', 'Move down')}
                    onClick={e => {
                      e.preventDefault();
                      moveRow({ from: idx, to: idx + 1 });
                    }}
                  >
                    <FontAwesomeIcon icon={faArrowDown} />
                  </button>
                )}
                {idx > 0 && (
                  <button
                    className="standalone"
                    type="button"
                    title={getTranslationFor('Move up', 'Move up')}
                    onClick={e => {
                      e.preventDefault();
                      moveRow({ from: idx, to: idx - 1 });
                    }}
                  >
                    <FontAwesomeIcon icon={faArrowUp} />
                  </button>
                )}
                <button
                  className="destructive"
                  type="button"
                  title={getTranslationFor('Delete', 'Delete')}
                  onClick={e => {
                    e.preventDefault();
                    removeRow(idx);
                  }}
                >
                  <FontAwesomeIcon icon={faTrash} />
                </button>
              </div>
            </div>
            <Collapse isOpened={expandedGroups[idx] === true}>
              <div className="row-content">
                <IntervalSelectorField value={entry} row={idx} />
                <DaysTableField value={entry} row={idx} />
              </div>
            </Collapse>
          </div>
        );
      })}
      <div className="data-footer">
        <button
          className="context"
          type="button"
          onClick={e => {
            e.preventDefault();
            toggleGroup(value.length);
            addRow();
          }}
        >
          <FontAwesomeIcon icon={faPlus} /> {getTranslationFor('Add')}
        </button>
      </div>
    </div>
  );
};
WidgetDataContainer.propTypes = {
  value: PropTypes.array,
  schema: PropTypes.object,
  vocabularies: PropTypes.object,
};

export default WidgetDataContainer;
