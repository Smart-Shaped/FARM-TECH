import React from 'react';

/**
 * Generic Table component inspired by GeoNode MapStore
 *
 * @param {Array} columns - Array of column definitions: [{ key, label, render?, className? }]
 * @param {Array} data - Array of data objects
 * @param {Function} onRowClick - Optional callback when clicking a row
 * @param {String} className - Additional CSS classes
 * @param {Boolean} striped - Enable striped rows
 * @param {Boolean} hover - Enable hover effect
 * @param {Boolean} bordered - Enable borders
 * @param {React.Node} emptyState - Content to show when data is empty
 */
export const Table = ({
    columns,
    data,
    onRowClick,
    className,
    striped,
    hover,
    bordered,
    emptyState
}) => {
    const tableClasses = [
        'table',
        striped && 'table-striped',
        hover && 'table-hover',
        bordered && 'table-bordered',
        className
    ].filter(Boolean).join(' ');

    if (!data || data.length === 0) {
        return (
            <div className="table-empty-state">
                {emptyState || <p className="text-muted text-center p-4">No data available</p>}
            </div>
        );
    }

    return (
        <div className="table-responsive">
            <table className={tableClasses}>
                <thead>
                    <tr>
                        {columns.map((column, index) => (
                            <th
                                key={column.key || index}
                                className={column.headerClassName}
                                style={column.headerStyle}
                            >
                                {column.label}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, rowIndex) => (
                        <tr
                            key={row.id || rowIndex}
                            onClick={() => onRowClick && onRowClick(row)}
                            style={{ cursor: onRowClick ? 'pointer' : 'default' }}
                        >
                            {columns.map((column, colIndex) => {
                                const cellValue = row[column.key];
                                const cellContent = column.render
                                    ? column.render(cellValue, row, rowIndex)
                                    : cellValue;

                                return (
                                    <td
                                        key={column.key || colIndex}
                                        className={column.className}
                                        style={column.style}
                                    >
                                        {cellContent}
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

