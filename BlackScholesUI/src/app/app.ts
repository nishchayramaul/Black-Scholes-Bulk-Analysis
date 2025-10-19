import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { FileUploader, ApiResponse } from './components/file-uploader/file-uploader';
import { ResultsTableComponent } from './components/results-table/results-table';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, FileUploader, ResultsTableComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('options-pricing');
  
  // Results data
  results: ApiResponse | null = null;
  showResults: boolean = false;
  loading: boolean = false;

  onUploadSuccess(data: ApiResponse): void {
    this.results = data;
    this.showResults = true;
    this.loading = false;
  }

  onUploadError(error: string): void {
    this.loading = false;
    console.error('Upload error:', error);
  }

  onUploadStart(): void {
    this.loading = true;
    this.showResults = false;
  }
}
