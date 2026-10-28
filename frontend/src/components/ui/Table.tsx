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
          'w-full text-left text-xs sm:text-sm text-slate-700 dark:text-slate-300 border-collapse tracking-tight',
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
        'bg-black/[0.02] dark:bg-white/[0.03] border-b border-black/[0.05] dark:border-white/[0.08] text-[11px] font-semibold text-slate-400 dark:text-slate-400 uppercase tracking-wider',
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
      className={clsx('divide-y divide-black/[0.04] dark:divide-white/[0.06]', className)}
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
        'transition-colors duration-150 hover:bg-black/[0.02] dark:hover:bg-white/[0.03]',
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
    <th
      className={clsx('px-4 py-3 font-semibold text-slate-400 dark:text-slate-400 tracking-wider', className)}
      {...props}
    >
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
    <td
      className={clsx('px-4 py-3 text-slate-700 dark:text-slate-200 align-middle', className)}
      {...props}
    >
      {children}
    </td>
  );
};
