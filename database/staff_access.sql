-- Staff credentials only. No shared/default credentials are seeded.
-- Matches the users structure in the project's historical MySQL backup.
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL UNIQUE,
    password_hash VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL,
    first_name VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL,
    last_name VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL,
    role ENUM('ADMIN', 'LYDO_OFFICIAL') NOT NULL DEFAULT 'LYDO_OFFICIAL',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
