-- MySQL Schema for Stock Monitor Application
-- Character set: utf8mb4 for full Unicode support
-- Engine: InnoDB for transaction support and row-level locking

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Stock items table for inventory management
CREATE TABLE IF NOT EXISTS stock_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    selling_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    description TEXT,
    image_path VARCHAR(255),
    total_initial_value DECIMAL(10,2) DEFAULT 0.00,
    current_stock_value DECIMAL(10,2) DEFAULT 0.00,
    initial_price DECIMAL(10,2) DEFAULT 0.00,
    added_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_added_by (added_by),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sales table for transaction records
CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT,
    item_name VARCHAR(255),
    quantity_sold INT NOT NULL DEFAULT 0,
    selling_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    image_path VARCHAR(255),
    user_id INT,
    user_name VARCHAR(50),
    user_email VARCHAR(100),
    place VARCHAR(100),
    sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_item_id (item_id),
    INDEX idx_user_id (user_id),
    INDEX idx_sold_at (sold_at),
    INDEX idx_item_name (item_name),
    FOREIGN KEY (item_id) REFERENCES stock_items(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Investment transactions table for investor tracking
CREATE TABLE IF NOT EXISTS investment_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_type ENUM('invest', 'withdraw') NOT NULL,
    amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    description TEXT,
    investor_name VARCHAR(100),
    investor_email VARCHAR(100),
    investor_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_investor_name (investor_name),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_created_at (created_at),
    INDEX idx_investor_email (investor_email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Wages table for employee payment tracking
CREATE TABLE IF NOT EXISTS wages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_name VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    wage_type VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_employee_name (employee_name),
    INDEX idx_wage_type (wage_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123)
INSERT IGNORE INTO users (username, password_hash, email) 
VALUES ('admin', 'pbkdf2:sha256:260000$salt$hash', 'admin@stockmonitor.com');

-- Add triggers for automatic stock value updates
DELIMITER //

CREATE TRIGGER IF NOT EXISTS update_stock_value_after_insert 
AFTER INSERT ON stock_items
FOR EACH ROW
BEGIN
    UPDATE stock_items 
    SET current_stock_value = quantity * selling_price 
    WHERE id = NEW.id;
END//

CREATE TRIGGER IF NOT EXISTS update_stock_value_after_update 
AFTER UPDATE ON stock_items
FOR EACH ROW
BEGIN
    UPDATE stock_items 
    SET current_stock_value = quantity * selling_price 
    WHERE id = NEW.id;
END//

DELIMITER ;
