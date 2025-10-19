import { Component, Output, EventEmitter } from '@angular/core';
import { HttpClient, HttpEventType, HttpErrorResponse } from '@angular/common/http';
import { CommonModule } from '@angular/common';

export interface ApiResponse {
  total_rows: number;
  successful_calculations: number;
  failed_calculations: number;
  results: any[];
}

@Component({
  selector: 'app-file-uploader',
  imports: [CommonModule],
  templateUrl: './file-uploader.html',
  styleUrl: './file-uploader.css'
})
export class FileUploader {
  selectedFile: File | null = null;
  message: string = '';
  progress: number = 0;
  isUploading: boolean = false;
  uploadUrl = '/api/v1/black-scholes/process-stream-parallel';
  
  // Allowed file extensions
  allowedExtensions = ['.csv', '.xlsx', '.xls'];
  
  // Output events
  @Output() uploadSuccess = new EventEmitter<ApiResponse>();
  @Output() uploadError = new EventEmitter<string>();
  
  constructor(private readonly http: HttpClient) {}

  onFileChange(event: any): void {
    const file = event.target.files[0];
    
    if (!file) {
      this.message = 'No file selected';
      return;
    }

    // Validate file extension
    const fileExtension = this.getFileExtension(file.name);
    if (!this.allowedExtensions.includes(fileExtension.toLowerCase())) {
      this.message = `Invalid file type. Please select a CSV or Excel file (.csv, .xlsx, .xls)`;
      this.selectedFile = null;
      return;
    }

    // Validate file size (50MB limit)
    const maxSize = 60 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      this.message = 'File size too large. Maximum size is 50MB';
      this.selectedFile = null;
      return;
    }

    this.selectedFile = file;
    this.message = `Selected: ${file.name} (${this.formatFileSize(file.size)})`;
    this.progress = 0;
  }

  onUpload(): void {
    if (!this.selectedFile) {
      this.message = 'Please select a file first';
      return;
    }

    this.isUploading = true;
    this.progress = 0;
    this.message = 'Uploading...';

    const formData = new FormData();
    formData.append('file', this.selectedFile);

    this.http.post<ApiResponse>(this.uploadUrl, formData, {
      reportProgress: true,
      observe: 'events'
    }).subscribe({
      next: (event: any) => {
        if (event.type === HttpEventType.UploadProgress) {
          this.progress = Math.round(100 * event.loaded / event.total!);
        } else if (event.type === HttpEventType.Response) {
          this.message = 'File uploaded successfully!';
          this.isUploading = false;
          this.selectedFile = null;
          // Reset file input
          const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
          if (fileInput) fileInput.value = '';
          // Emit success event with results
          this.uploadSuccess.emit(event.body);
        }
      },
      error: (error: HttpErrorResponse) => {
        this.isUploading = false;
        this.message = `Upload failed: ${error.error?.message || error.message}`;
        this.progress = 0;
        // Emit error event
        this.uploadError.emit(this.message);
      }
    });
  }

  private getFileExtension(filename: string): string {
    const lastDotIndex = filename.lastIndexOf('.');
    if (lastDotIndex === -1) return '';
    return filename.slice(lastDotIndex);
  }

  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}
