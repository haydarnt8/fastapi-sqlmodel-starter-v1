# Internationalization (i18n) Guide

This API supports multilingual content with Arabic (ar) and English (en) languages.

## Features

- Automatic language detection from query parameters or headers
- Translation system for API messages and responses
- Support for English (en) and Arabic (ar)
- Easy to extend with more languages

## Language Detection

The system detects the user's preferred language in the following priority order:

1. **Query Parameter**: `?lang=ar` or `?lang=en`
2. **Accept-Language Header**: `Accept-Language: ar` or `Accept-Language: en`
3. **Default**: English (`en`)

## Usage in API Endpoints

### Method 1: Using Dependency Injection

```python
from fastapi import APIRouter, Depends, Request
from app.i18n import Translator
from app.api.deps import get_translation

router = APIRouter()

@router.get("/example")
async def example_endpoint(
    request: Request,
    t: Translator = Depends(get_translation)
):
    """
    Example endpoint with translation support.

    Try:
    - GET /example
    - GET /example?lang=ar
    - GET /example with header Accept-Language: ar
    """
    return {
        "message": t("common.success"),
        "user_created": t("user.user_created"),
        "login_failed": t("auth.login_failed"),
    }
```

### Method 2: Manual Translator

```python
from fastapi import APIRouter, Request
from app.i18n import get_translator

router = APIRouter()

@router.get("/example")
async def example_endpoint(request: Request):
    # Get translator for current request
    t = get_translator(request)

    return {
        "message": t("common.success"),
        "description": t("role.description"),
    }
```

### Method 3: Direct Translation with Formatting

```python
from app.i18n import Translator

t = Translator("ar")  # Arabic translator

# Simple translation
message = t("common.success")  # Returns: "نجح"

# Translation with variables
min_length_msg = t("validation.min_length", min=8)
# Returns: "الحد الأدنى للطول هو 8"
```

## Available Translation Keys

### Common Messages
- `common.success` - Success
- `common.error` - Error
- `common.created` - Created successfully
- `common.updated` - Updated successfully
- `common.deleted` - Deleted successfully
- `common.not_found` - Resource not found
- `common.validation_error` - Validation error
- `common.unauthorized` - Unauthorized
- `common.forbidden` - Forbidden

### Authentication
- `auth.login_success` - Login successful
- `auth.login_failed` - Invalid email or password
- `auth.logout_success` - Logout successful
- `auth.token_expired` - Token has expired
- `auth.token_invalid` - Invalid token
- `auth.password_min_length` - Password minimum length message

### User Management
- `user.user_created` - User created successfully
- `user.user_updated` - User updated successfully
- `user.user_deleted` - User deleted successfully
- `user.user_not_found` - User not found
- `user.email_exists` - Email already exists
- `user.invalid_email` - Invalid email format

### Role Management
- `role.role_created` - Role created successfully
- `role.role_updated` - Role updated successfully
- `role.role_deleted` - Role deleted successfully
- `role.role_not_found` - Role not found
- `role.cannot_delete_system_role` - Cannot delete system role

### Permissions
- `permission.permission_assigned` - Permission assigned successfully
- `permission.permission_removed` - Permission removed successfully
- `permission.permission_not_found` - Permission not found

### Validation
- `validation.required` - This field is required
- `validation.invalid_format` - Invalid format
- `validation.min_length` - Minimum length is {min}
- `validation.max_length` - Maximum length is {max}

## Adding New Translations

### 1. Add to English (`app/i18n/locales/en.json`)

```json
{
  "product": {
    "product_created": "Product created successfully",
    "product_not_found": "Product not found",
    "price_must_be_positive": "Price must be positive"
  }
}
```

### 2. Add to Arabic (`app/i18n/locales/ar.json`)

```json
{
  "product": {
    "product_created": "تم إنشاء المنتج بنجاح",
    "product_not_found": "المنتج غير موجود",
    "price_must_be_positive": "يجب أن يكون السعر موجباً"
  }
}
```

### 3. Use in Code

```python
from app.i18n import get_translator

@router.post("/products")
async def create_product(request: Request, product_data: ProductCreate):
    t = get_translator(request)

    # Create product
    product = await product_crud.create(session, obj_in=product_data)

    return {
        "message": t("product.product_created"),
        "data": product
    }
```

## Adding a New Language

### 1. Create Translation File

Create `app/i18n/locales/fr.json` for French:

```json
{
  "common": {
    "success": "Succès",
    "error": "Erreur"
  }
}
```

### 2. Update Supported Languages

Edit `app/i18n/translator.py`:

```python
# Change from:
SUPPORTED_LANGUAGES = ["en", "ar"]

# To:
SUPPORTED_LANGUAGES = ["en", "ar", "fr"]
```

### 3. Restart Application

The new language will be loaded automatically on startup.

## Testing Translations

### Using curl (Query Parameter)

```bash
# English (default)
curl -X GET "http://localhost:8000/api/v1/roles" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Arabic
curl -X GET "http://localhost:8000/api/v1/roles?lang=ar" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using curl (Header)

```bash
# Arabic via header
curl -X GET "http://localhost:8000/api/v1/roles" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept-Language: ar"
```

### Using the Test Script

```bash
chmod +x test_i18n.sh
./test_i18n.sh
```

## Translation System Architecture

```
app/
├── i18n/
│   ├── __init__.py          # Module exports
│   ├── translator.py        # Core translation logic
│   └── locales/
│       ├── en.json         # English translations
│       └── ar.json         # Arabic translations
├── api/
│   └── deps.py             # get_translation dependency
└── main.py                 # Load translations at startup
```

## Best Practices

1. **Always use translation keys** - Never hardcode strings in responses
2. **Group related translations** - Use logical namespaces (auth, user, product)
3. **Use descriptive keys** - `user.email_exists` is better than `user.err1`
4. **Keep translations consistent** - Use the same tone and terminology
5. **Test both languages** - Ensure translations are accurate and complete
6. **Use variables for dynamic content** - `"Hello {name}"` instead of string concatenation

## Common Patterns

### Success Response
```python
return {
    "message": t("common.success"),
    "data": result
}
```

### Error Response
```python
raise HTTPException(
    status_code=404,
    detail=t("user.user_not_found")
)
```

### Validation Error
```python
if len(password) < 8:
    raise HTTPException(
        status_code=400,
        detail=t("auth.password_min_length")
    )
```

## Current Limitations

1. **Database content is not translated** - Role names, descriptions, etc. are stored in the database in one language
2. **Translations are in JSON files** - Not stored in database (simpler, but less dynamic)
3. **No plural forms** - Current system doesn't handle pluralization

## Future Enhancements

1. **Database-backed translations** - Store translations in database for dynamic updates
2. **Pluralization support** - Handle singular/plural forms correctly
3. **Date/time formatting** - Locale-specific date and time formats
4. **Currency formatting** - Locale-specific currency display
5. **RTL support** - Right-to-left text direction for Arabic
6. **Translation management UI** - Admin interface to manage translations

## Support

For questions or issues with the translation system, please refer to:
- Translation files: `app/i18n/locales/`
- Core logic: `app/i18n/translator.py`
- Dependencies: `app/api/deps.py`
- Startup: `app/main.py`
