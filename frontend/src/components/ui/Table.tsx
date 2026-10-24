import React from 'react';
import { clsx } from 'clsx';

export const Table: React.FC<React.TableHTMLAttributes<HTMLTableElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <div className="w-full overflow-x-auto">
      <table
        className={clsx(
          'w-full text-left text-sm text-slate-700 dark:text-slate-300 border-collapse',
          className
        )}
        {...props}
      >
        {children}
      </table>
    </div>
  );
};

export const TableHeader: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <thead
      className={clsx(
        'bg-slate-50/75 dark:bg-cricket-navy-950/60 border-b border-slate-200 dark:border-cricket-navy-800 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider',
        className
      )}
      {...props}
    >
      {children}
    </thead>
  );
};

export const TableBody: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <tbody
      className={clsx('divide-y divide-slate-100 dark:divide-cricket-navy-800/80', className)}
      {...props}
    >
      {children}
    </tbody>
  );
};

export const TableRow: React.FC<React.HTMLAttributes<HTMLTableRowElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <tr
      className={clsx(
        'hover:bg-slate-50/70 dark:hover:bg-cricket-navy-800/40 transition-colors',
        className
      )}
      {...props}
    >
      {children}
    </tr>
  );
};

export const TableHead: React.FC<React.ThHTMLAttributes<HTMLTableCellElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <th className={clsx('px-4 py-3 font-medium whitespace-nowrap', className)} {...props}>
      {children}
    </th>
  );
};

export const TableCell: React.FC<React.TdHTMLAttributes<HTMLTableCellElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <td className={clsx('px-4 py-3 whitespace-nowrap', className)} {...props}>
      {children}
    </td>
  );
};
