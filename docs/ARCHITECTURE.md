# Architecture Overview

## Current Implementation (Phase 1)

### System Flow

```
┌─────────────┐
│   Upload    │
│   Invoice   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Save File  │
│  (Temp)     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  PaddleOCR  │
│  Extract    │
│  Text       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Regex     │
│  Pattern    │
│  Matching   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Return    │
│    JSON     │
└─────────────┘
```

### Components

#### 1. FastAPI Backend (`backend/main.py`)

**Responsibilities:**
- Handle file uploads
- Coordinate OCR and extraction
- Return structured JSON
- Error handling and logging

**Key Features:**
- CORS enabled for frontend integration
- Temporary file handling
- Comprehensive error messages

#### 2. OCR Layer (PaddleOCR)

**Function:** `extract_text_from_image()`

**Input:** Image file path  
**Output:** Raw text string

**Why PaddleOCR?**
- Fast and accurate
- No API costs
- Runs locally
- Supports multiple languages

#### 3. Extraction Layer (Regex)

**Function:** `extract_invoice_fields()`

**Input:** Raw text  
**Output:** Structured dictionary

**Current Fields:**
- `invoice_number`
- `date`
- `total_amount`

**Approach:**
- Multiple regex patterns per field
- Fallback patterns for robustness
- Simple heuristics (e.g., max amount for total)

### Design Decisions

#### Why Start Simple?

1. **Validate the flow** - Ensure end-to-end works
2. **Fast iteration** - No model training delays
3. **Clear baseline** - Easy to measure improvements
4. **Production-ready structure** - Clean separation of concerns

#### What's NOT Included (Yet)

- ❌ Machine learning models
- ❌ Database storage
- ❌ Async processing
- ❌ Feedback system
- ❌ Confidence scoring
- ❌ Multiple document types

## Future Architecture (Planned)

### Phase 2: Feedback Loop

```
Upload → OCR → Extract → JSON → User Feedback → Dataset
                                      ↓
                                  Retrain Model
```

**Components to Add:**
- Feedback collection endpoint
- Database for storing corrections
- Dataset builder
- Model training pipeline

### Phase 3: ML Enhancement

**Replace regex with:**
- Named Entity Recognition (NER)
- Custom trained models
- Confidence scoring
- Multi-field extraction

### Phase 4: Production Scale

**Infrastructure:**
- PostgreSQL for data persistence
- Redis + Celery for async processing
- Docker containerization
- Monitoring and logging
- Rate limiting
- Authentication

## Code Structure

```
adaptive-document-intelligence/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── requirements.txt     # Dependencies
│   └── test_api.py         # Test script
├── docs/
│   ├── SETUP.md            # Installation guide
│   ├── API.md              # API documentation
│   ├── USAGE.md            # Usage examples
│   └── ARCHITECTURE.md     # This file
├── .gitignore
├── LICENSE
└── README.md
```

## Technology Choices

### Backend: FastAPI

**Why?**
- Modern Python framework
- Automatic API documentation
- Type hints and validation
- Async support (for future)
- Easy to test

### OCR: PaddleOCR

**Why?**
- Open source
- No API costs
- Fast inference
- Good accuracy
- Active development

### Extraction: Regex (Phase 1)

**Why start with regex?**
- Zero setup time
- Predictable behavior
- Easy to debug
- Good for common patterns
- Fast iteration

**When to switch to ML?**
- After collecting real data
- When patterns become complex
- When accuracy matters more than speed

## Performance Considerations

### Current Bottlenecks

1. **OCR Processing** - Takes 1-3 seconds per image
2. **Synchronous** - Blocks during processing

### Future Optimizations

1. **Async Processing** - Use Celery for background jobs
2. **Caching** - Cache OCR results
3. **Batch Processing** - Process multiple files
4. **Model Optimization** - Quantization, pruning

## Security Considerations

### Current

- File type validation
- Temporary file cleanup
- Error message sanitization

### Future

- Authentication/Authorization
- Rate limiting
- File size limits
- Virus scanning
- Input sanitization