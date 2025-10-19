import { Component, Input, Output, EventEmitter, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface BlackScholesResult {
  row_index: number;
  input_data: {
    S: number;
    K: number;
    T: number;
    r: number;
    sigma: number;
    option_type: string;
  };
  calculated_values: {
    option_price: number;
    greeks: {
      delta: number;
      gamma: number;
      theta: number;
      vega: number;
      rho: number;
    };
  };
  error: string | null;
}

export interface ApiResponse {
  total_rows: number;
  successful_calculations: number;
  failed_calculations: number;
  results: BlackScholesResult[];
}

@Component({
  selector: 'app-results-table',
  imports: [CommonModule, FormsModule],
  templateUrl: './results-table.html',
  styleUrl: './results-table.css'
})
export class ResultsTableComponent implements OnInit, OnChanges {
  @Input() data: ApiResponse | null = null;
  @Input() loading: boolean = false;
  @Output() pageChange = new EventEmitter<number>();
  @Output() pageSizeChange = new EventEmitter<number>();

  // Pagination
  currentPage: number = 1;
  pageSize: number = 20;
  pageSizeOptions: number[] = [10, 20, 50, 100];
  totalPages: number = 0;
  paginatedResults: BlackScholesResult[] = [];

  // Table columns configuration
  columns = [
    { key: 'row_index', label: 'Row', width: 60, minWidth: 50 },
    { key: 'S', label: 'Stock Price (S)', width: 120, minWidth: 80 },
    { key: 'K', label: 'Strike Price (K)', width: 120, minWidth: 80 },
    { key: 'T', label: 'Time to Expiry (T)', width: 140, minWidth: 100 },
    { key: 'r', label: 'Risk-free Rate (r)', width: 140, minWidth: 100 },
    { key: 'sigma', label: 'Volatility (σ)', width: 120, minWidth: 80 },
    { key: 'option_type', label: 'Option Type', width: 100, minWidth: 80 },
    { key: 'option_price', label: 'Option Price', width: 120, minWidth: 100 },
    { key: 'delta', label: 'Delta', width: 100, minWidth: 80 },
    { key: 'gamma', label: 'Gamma', width: 100, minWidth: 80 },
    { key: 'theta', label: 'Theta', width: 100, minWidth: 80 },
    { key: 'vega', label: 'Vega', width: 100, minWidth: 80 },
    { key: 'rho', label: 'Rho', width: 100, minWidth: 80 }
  ];

  // Column resizing and dragging
  isResizing: boolean = false;
  isDragging: boolean = false;
  resizingColumn: number = -1;
  dragStartColumn: number = -1;
  dragOverColumn: number = -1;
  startX: number = 0;
  startWidth: number = 0;

  ngOnInit(): void {
    this.updatePagination();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['data'] && this.data) {
      this.currentPage = 1;
      this.updatePagination();
    }
  }

  updatePagination(): void {
    if (!this.data?.results) {
      this.paginatedResults = [];
      this.totalPages = 0;
      return;
    }

    // Ensure pageSize is always a number
    const pageSize = Number(this.pageSize);
    this.totalPages = Math.ceil(this.data.results.length / pageSize);
    const startIndex = (this.currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    this.paginatedResults = this.data.results.slice(startIndex, endIndex);
  }

  onPageChange(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.updatePagination();
      this.pageChange.emit(page);
    }
  }

  onPageSizeChange(): void {
    // Convert pageSize to number to ensure proper calculation
    const newPageSize = Number(this.pageSize);
    
    // Calculate which record we're currently viewing
    const currentRecordIndex = (this.currentPage - 1) * this.pageSize;
    
    // Calculate which page this record should be on with the new page size
    const newPage = Math.floor(currentRecordIndex / newPageSize) + 1;
    
    this.pageSize = newPageSize;
    this.currentPage = newPage;
    this.updatePagination();
    this.pageSizeChange.emit(this.pageSize);
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(this.totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    return pages;
  }

  getCellValue(result: BlackScholesResult, columnKey: string): any {
    switch (columnKey) {
      case 'row_index':
        return result.row_index;
      case 'S':
      case 'K':
      case 'T':
      case 'r':
      case 'sigma':
      case 'option_type':
        return result.input_data[columnKey];
      case 'option_price':
        return result.calculated_values.option_price;
      case 'delta':
      case 'gamma':
      case 'theta':
      case 'vega':
      case 'rho':
        return result.calculated_values.greeks[columnKey];
      default:
        return '';
    }
  }

  formatNumber(value: any, columnKey?: string): string {
    if (typeof value === 'number') {
      // Row index should be displayed as whole number
      if (columnKey === 'row_index') {
        return value.toString();
      }
      // Other numbers with 4 decimal places
      return value.toFixed(4);
    }
    return value?.toString() || '';
  }

  getSummaryStats(): { total: number; successful: number; failed: number } {
    if (!this.data) return { total: 0, successful: 0, failed: 0 };
    return {
      total: this.data.total_rows,
      successful: this.data.successful_calculations,
      failed: this.data.failed_calculations
    };
  }

  getMathMin(a: number, b: number): number {
    return Math.min(a, b);
  }

  // Column resizing methods
  onResizeStart(event: MouseEvent, columnIndex: number): void {
    event.preventDefault();
    this.isResizing = true;
    this.resizingColumn = columnIndex;
    this.startX = event.clientX;
    this.startWidth = this.columns[columnIndex].width;
    
    document.addEventListener('mousemove', this.onResizeMove.bind(this));
    document.addEventListener('mouseup', this.onResizeEnd.bind(this));
    document.body.classList.add('resizing');
  }

  onResizeMove(event: MouseEvent): void {
    if (!this.isResizing) return;
    
    const deltaX = event.clientX - this.startX;
    const newWidth = Math.max(this.columns[this.resizingColumn].minWidth, this.startWidth + deltaX);
    this.columns[this.resizingColumn].width = newWidth;
  }

  onResizeEnd(): void {
    this.isResizing = false;
    this.resizingColumn = -1;
    
    document.removeEventListener('mousemove', this.onResizeMove.bind(this));
    document.removeEventListener('mouseup', this.onResizeEnd.bind(this));
    document.body.classList.remove('resizing');
  }

  // Column dragging methods
  onDragStart(event: DragEvent, columnIndex: number): void {
    this.isDragging = true;
    this.dragStartColumn = columnIndex;
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', columnIndex.toString());
    }
  }

  onDragOver(event: DragEvent, columnIndex: number): void {
    event.preventDefault();
    this.dragOverColumn = columnIndex;
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'move';
    }
  }

  onDragLeave(): void {
    this.dragOverColumn = -1;
  }

  onDrop(event: DragEvent, targetColumnIndex: number): void {
    event.preventDefault();
    
    if (this.dragStartColumn !== -1 && this.dragStartColumn !== targetColumnIndex) {
      // Swap columns
      const draggedColumn = this.columns[this.dragStartColumn];
      this.columns.splice(this.dragStartColumn, 1);
      this.columns.splice(targetColumnIndex, 0, draggedColumn);
    }
    
    this.isDragging = false;
    this.dragStartColumn = -1;
    this.dragOverColumn = -1;
  }

  onDragEnd(): void {
    this.isDragging = false;
    this.dragStartColumn = -1;
    this.dragOverColumn = -1;
  }

  getColumnWidth(column: any): string {
    return column.width + 'px';
  }

  isColumnBeingDragged(columnIndex: number): boolean {
    return this.dragStartColumn === columnIndex;
  }

  isColumnDropTarget(columnIndex: number): boolean {
    return this.dragOverColumn === columnIndex && this.dragStartColumn !== columnIndex;
  }

  isColumnBeingResized(columnIndex: number): boolean {
    return this.resizingColumn === columnIndex;
  }
}
