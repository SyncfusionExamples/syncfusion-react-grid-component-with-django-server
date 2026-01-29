import React, { useMemo, useRef } from 'react';
import {
  GridComponent,
  ColumnsDirective,
  ColumnDirective,
  Page,
  Sort,
  Filter,
  Edit,
  Toolbar,
  Search,
  Inject,
  type EditSettingsModel,
  type FilterSettingsModel,
  type SelectionSettingsModel,
  type ToolbarItems,
} from '@syncfusion/ej2-react-grids';
import { DataManager, UrlAdaptor } from '@syncfusion/ej2-data';
import './App.css';

type DueState = 'returned' | 'overdue' | 'due' | 'today' | 'unknown';

const App: React.FC = () => {
  const gridRef = useRef<GridComponent | null>(null);

  // DataManager (Django REST endpoint)
  const data = useMemo(
    () =>
      new DataManager({
        url: 'http://localhost:8000/api/lendings/',
        adaptor: new UrlAdaptor(),
        crossDomain: true,
      }),
    []
  );

  // Paging
  const pageSettings = useMemo(() => ({ pageSize: 12, pageSizes: [10, 12, 20, 50, 100] }), []);

  // Filtering
  const filterSettings: FilterSettingsModel = useMemo(() => ({ type: 'Excel' }), []);
  const menuFilterSettings = useMemo(() => ({ type: 'Menu' as const }), []);
  const checkBoxFilterSettings = useMemo(() => ({ type: 'CheckBox' as const }), []);

  // Toolbar
  const toolbar: ToolbarItems[] = useMemo(
    () => ['Add', 'Edit', 'Delete', 'Update', 'Cancel', 'Search'],
    []
  );

  // Editing
  const editSettings: EditSettingsModel = useMemo(
    () => ({
      allowAdding: true,
      allowEditing: true,
      allowDeleting: true,
    }),
    []
  );

  // Selection
  const selectionSettings: SelectionSettingsModel = useMemo(
    () => ({ type: 'Single', mode: 'Row' }),
    []
  );

  // ===== Helpers =====
  const parseDate = (d: any): Date | null => {
    if (!d) return null;
    const dt = new Date(d);
    return isNaN(dt.getTime()) ? null : dt;
  };

  const stripTime = (d: Date): Date => {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  };

  const getDueMeta = (row: any): { label: string; state: DueState } => {
    const due = parseDate(row?.expected_return_date);
    const ret = parseDate(row?.actual_return_date);
    if (!due && !ret) return { label: '—', state: 'unknown' };
    if (ret) return { label: `Returned ${ret.toLocaleDateString()}`, state: 'returned' };

    if (!due) return { label: '—', state: 'unknown' };

    const today = stripTime(new Date());
    const d0 = stripTime(due);
    const diffDays = Math.floor((d0.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays > 0) return { label: `Due in ${diffDays} day${diffDays === 1 ? '' : 's'}`, state: 'due' };
    if (diffDays === 0) return { label: 'Due today', state: 'today' };
    return { label: `Overdue by ${Math.abs(diffDays)} day${Math.abs(diffDays) === 1 ? '' : 's'}`, state: 'overdue' };
  };

  const getStatusClass = (status?: string | null): string => {
    const s = (status || '').toLowerCase();
    if (s === 'returned') return 'pill pill--returned';
    if (s === 'borrowed') return 'pill pill--borrowed';
    if (s === 'overdue') return 'pill pill--overdue';
    if (s === 'lost') return 'pill pill--lost';
    return 'pill';
  };

  const getGenreClass = (genre?: string | null): string => {
    const g = (genre || '').toLowerCase();
    if (g === 'fantasy') return 'gchip g-fantasy';
    if (g === 'science fiction') return 'gchip g-scifi';
    if (g === 'mystery') return 'gchip g-mystery';
    if (g === 'thriller') return 'gchip g-thriller';
    if (g === 'romance') return 'gchip g-romance';
    if (g === 'historical') return 'gchip g-historical';
    if (g === 'non-fiction') return 'gchip g-nonfiction';
    if (g === 'biography') return 'gchip g-biography';
    if (g === 'young adult') return 'gchip g-ya';
    if (g === 'horror') return 'gchip g-horror';
    if (g === 'adventure') return 'gchip g-adventure';
    if (g === 'classic') return 'gchip g-classic';
    return 'gchip';
  };

  // ===== Column templates (React) =====
  const GenreTemplate = (data: any) => (
    <span className={getGenreClass(data.genre)} title={data.genre || '—'}>
      {data.genre || '—'}
    </span>
  );

  const EmailTemplate = (data: any) => (
    <a href={`mailto:${data.borrower_email}`} title={data.borrower_email}>
      {data.borrower_email}
    </a>
  );

  const BorrowedDateTemplate = (data: any) => {
    const d = parseDate(data.borrowed_date);
    const label = d ? d.toLocaleDateString('en-US') : '—';
    return (
      <span className="chip chip--outline" title={label}>
        {label}
      </span>
    );
  };

  const ExpectedReturnTemplate = (data: any) => {
    const due = getDueMeta(data);
    const cls =
      `chip chip--date ${
        due.state === 'returned'
          ? 'is-returned'
          : due.state === 'overdue'
          ? 'is-overdue'
          : due.state === 'due'
          ? 'is-due'
          : due.state === 'today'
          ? 'is-today'
          : 'is-unknown'
      }`;
    return (
      <span className={cls} title={due.label}>
        {due.label}
      </span>
    );
  };

  const ActualReturnTemplate = (data: any) => {
    const d = parseDate(data.actual_return_date);
    if (!d) {
      return <span className="chip chip--date is-unknown">—</span>;
    }
    const label = `Returned ${d.toLocaleDateString('en-US')}`;
    return (
      <span className="chip chip--date is-returned" title={label}>
        ✔ {d.toLocaleDateString('en-US')}
      </span>
    );
  };

  const StatusTemplate = (data: any) => {
    const cls = getStatusClass(data.lending_status);
    return (
      <span className={cls} title={data.lending_status || 'Unknown'}>
        {data.lending_status || 'Unknown'}
      </span>
    );
  };

  // Validation rules (same as Angular)
  const authorNameValidationRule = { required: true, minLength: 3, maxLength: 50 };
  const bookTitleValidationRule = { required: true, minLength: 1, maxLength: 100 };
  const ISBNValidationRule = { required: true, minLength: 10, maxLength: 13 };
  const genreValidationRule = { required: true };
  const borrowerNameValidationRule = { required: true, minLength: 3, maxLength: 50 };
  const borrowerEmailValidationRule = { required: true, email: true };
  const borrowDateValidationRule = { required: true };
  const expectedReturnDateValidationRule = { required: true };
  const lendingStatusValidationRule = { required: true };

  return (
    <div style={{ padding: 16 }}>
      <GridComponent
        ref={gridRef}
        dataSource={data}
        allowPaging={true}
        pageSettings={pageSettings}
        allowSorting={true}
        allowFiltering={true}
        filterSettings={filterSettings}
        toolbar={toolbar}
        editSettings={editSettings}
        selectionSettings={selectionSettings}
        gridLines="Both"
      >
        <ColumnsDirective>
          <ColumnDirective
            field="record_id"
            headerText="Record ID"
            width="120"
            isPrimaryKey={true}
            visible={false}
          />

          <ColumnDirective
            field="isbn_number"
            headerText="ISBN Number"
            width="170"
            validationRules={ISBNValidationRule}
          />

          <ColumnDirective
            field="book_title"
            headerText="Book Title"
            width="240"
            validationRules={bookTitleValidationRule}
          />

          <ColumnDirective
            field="author_name"
            headerText="Author Name"
            width="200"
            validationRules={authorNameValidationRule}
          />

          <ColumnDirective
            field="genre"
            headerText="Genre"
            width="160"
            editType="dropdownedit"
            textAlign="Center"
            filter={checkBoxFilterSettings}
            validationRules={genreValidationRule}
            template={GenreTemplate}
          />

          <ColumnDirective
            field="borrower_name"
            headerText="Borrower Name"
            width="200"
            validationRules={borrowerNameValidationRule}
          />

          <ColumnDirective
            field="borrower_email"
            headerText="Borrower Email"
            width="240"
            validationRules={borrowerEmailValidationRule}
            template={EmailTemplate}
          />

          <ColumnDirective
            field="borrowed_date"
            headerText="Borrowed Date"
            width="160"
            type="date"
            format="yMd"
            editType="datepickeredit"
            textAlign="Right"
            filter={menuFilterSettings}
            validationRules={borrowDateValidationRule}
            template={BorrowedDateTemplate}
          />

          <ColumnDirective
            field="expected_return_date"
            headerText="Expected Return Date"
            width="200"
            type="date"
            format="yMd"
            editType="datepickeredit"
            textAlign="Right"
            filter={menuFilterSettings}
            validationRules={expectedReturnDateValidationRule}
            template={ExpectedReturnTemplate}
          />

          <ColumnDirective
            field="actual_return_date"
            headerText="Actual Return Date"
            width="190"
            type="date"
            editType="datepickeredit"
            textAlign="Right"
            filter={menuFilterSettings}
            template={ActualReturnTemplate}
          />

          <ColumnDirective
            field="lending_status"
            headerText="Lending Status"
            width="160"
            editType="dropdownedit"
            textAlign="Center"
            filter={checkBoxFilterSettings}
            validationRules={lendingStatusValidationRule}
            template={StatusTemplate}
          />
        </ColumnsDirective>

        <Inject services={[Page, Sort, Filter, Edit, Toolbar, Search]} />
      </GridComponent>
    </div>
  );
};

export default App;