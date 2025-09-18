# Requirements Document

## Introduction

This document outlines the requirements for porting the existing PHP-based comix-server to Python. The comix-server is a streaming server for comic books that serves manga/comic collections to iOS AirComix app clients. The Python port should maintain full compatibility with the existing AirComix protocol while providing better performance, maintainability, and modern deployment options.

The original PHP server runs on Apache with custom URL routing and serves comic archives (ZIP, CBZ, RAR, CBR) and individual image files through a REST-like API. The Python version should replicate this functionality using modern Python web frameworks.

## Requirements

### Requirement 1: Core Server Functionality

**User Story:** As a comic reader, I want to access my comic collection through the AirComix iOS app using a Python-based server, so that I can read comics with the same experience as the PHP version.

#### Acceptance Criteria

1. WHEN the server starts THEN it SHALL listen on a configurable port (default 31257)
2. WHEN a client connects to the root endpoint THEN the server SHALL return the manga directory name
3. WHEN the server receives requests THEN it SHALL maintain compatibility with the AirComix iOS app protocol
4. WHEN the server processes requests THEN it SHALL handle URL encoding/decoding properly
5. WHEN the server encounters errors THEN it SHALL return appropriate HTTP status codes

### Requirement 2: Directory and File Listing

**User Story:** As a comic reader, I want to browse through my comic collection directory structure, so that I can navigate to specific comics or series.

#### Acceptance Criteria

1. WHEN a client requests a directory path THEN the server SHALL return a newline-separated list of files and subdirectories
2. WHEN listing directory contents THEN the server SHALL filter out hidden files (starting with ".", "@eaDir", "Thumbs.db", ".DS_Store")
3. WHEN listing directory contents THEN the server SHALL filter out system directories ("__MACOSX")
4. WHEN listing directory contents THEN the server SHALL only show supported file types (images and archives)
5. WHEN a directory is empty or inaccessible THEN the server SHALL return an empty response
6. WHEN listing files THEN the server SHALL support nested directory structures

### Requirement 3: Archive File Support

**User Story:** As a comic reader, I want to access comics stored in archive formats (ZIP, CBZ, RAR, CBR), so that I don't need to extract files manually.

#### Acceptance Criteria

1. WHEN a client requests an archive file THEN the server SHALL return a list of image files within the archive
2. WHEN processing ZIP/CBZ files THEN the server SHALL use Python's zipfile module
3. WHEN processing RAR/CBR files THEN the server SHALL use appropriate RAR handling library
4. WHEN listing archive contents THEN the server SHALL filter out non-image files
5. WHEN archive files are corrupted THEN the server SHALL return appropriate error responses
6. WHEN archive file paths end with "/" THEN the server SHALL handle the trailing slash gracefully

### Requirement 4: Image Streaming

**User Story:** As a comic reader, I want to view individual images from comics (both from archives and direct files), so that I can read the comic content.

#### Acceptance Criteria

1. WHEN a client requests an image file THEN the server SHALL return the image with correct MIME type headers
2. WHEN serving images from archives THEN the server SHALL extract and stream the image without saving to disk
3. WHEN serving direct image files THEN the server SHALL stream the file efficiently
4. WHEN serving images THEN the server SHALL set appropriate Content-Type headers (image/jpeg, image/png, etc.)
5. WHEN serving images THEN the server SHALL set Content-Length headers when possible
6. WHEN image files don't exist THEN the server SHALL return 404 status code

### Requirement 5: File Format Support

**User Story:** As a comic reader, I want the server to support all common comic and image formats, so that I can access my entire collection regardless of format.

#### Acceptance Criteria

1. WHEN processing files THEN the server SHALL support image formats: JPG, JPEG, GIF, PNG, TIF, TIFF, BMP
2. WHEN processing files THEN the server SHALL support archive formats: ZIP, CBZ, RAR, CBR
3. WHEN determining file types THEN the server SHALL use case-insensitive extension matching
4. WHEN encountering unsupported file types THEN the server SHALL ignore them in listings
5. WHEN file extensions are missing THEN the server SHALL treat them as directories if they exist as directories

### Requirement 6: Character Encoding Support

**User Story:** As a comic reader with international comic collections, I want proper handling of non-ASCII filenames, so that I can access comics with Korean, Japanese, or other international characters.

#### Acceptance Criteria

1. WHEN processing filenames THEN the server SHALL handle UTF-8 encoding properly
2. WHEN processing archive entries THEN the server SHALL attempt to detect and convert character encodings
3. WHEN encoding conversion fails THEN the server SHALL fall back to the original filename
4. WHEN serving file lists THEN the server SHALL ensure proper UTF-8 output encoding
5. WHEN handling legacy archives THEN the server SHALL support common legacy encodings (EUC-KR, etc.)

### Requirement 7: Server Information Endpoint

**User Story:** As an AirComix app, I want to query server capabilities, so that I can determine what features are supported.

#### Acceptance Criteria

1. WHEN a client requests "/welcome.102" THEN the server SHALL return server capability information
2. WHEN returning capabilities THEN the server SHALL indicate "allowDownload=True"
3. WHEN returning capabilities THEN the server SHALL indicate "allowImageProcess=True"
4. WHEN returning capabilities THEN the server SHALL include a server identification message
5. WHEN the welcome endpoint is accessed THEN the server SHALL return plain text format

### Requirement 8: Configuration Management

**User Story:** As a server administrator, I want to configure the server settings easily, so that I can customize it for my environment.

#### Acceptance Criteria

1. WHEN starting the server THEN it SHALL read configuration from a config file or environment variables
2. WHEN configuring THEN the server SHALL allow setting the manga directory path
3. WHEN configuring THEN the server SHALL allow setting the server port
4. WHEN configuring THEN the server SHALL allow enabling/disabling debug mode
5. WHEN configuration is invalid THEN the server SHALL provide clear error messages
6. WHEN no configuration is provided THEN the server SHALL use sensible defaults

### Requirement 9: Error Handling and Logging

**User Story:** As a server administrator, I want proper error handling and logging, so that I can troubleshoot issues and monitor server health.

#### Acceptance Criteria

1. WHEN errors occur THEN the server SHALL log them with appropriate severity levels
2. WHEN files are not found THEN the server SHALL return HTTP 404 status
3. WHEN access is denied THEN the server SHALL return HTTP 403 status
4. WHEN server errors occur THEN the server SHALL return HTTP 500 status
5. WHEN debug mode is enabled THEN the server SHALL provide detailed error information
6. WHEN in production mode THEN the server SHALL not expose internal error details

### Requirement 10: Performance and Security

**User Story:** As a server administrator, I want the server to be secure and performant, so that it can handle multiple clients efficiently and safely.

#### Acceptance Criteria

1. WHEN serving files THEN the server SHALL prevent directory traversal attacks
2. WHEN processing requests THEN the server SHALL validate and sanitize input paths
3. WHEN streaming large files THEN the server SHALL use efficient streaming methods
4. WHEN handling multiple requests THEN the server SHALL support concurrent connections
5. WHEN accessing files THEN the server SHALL respect file system permissions
6. WHEN serving content THEN the server SHALL set appropriate security headers