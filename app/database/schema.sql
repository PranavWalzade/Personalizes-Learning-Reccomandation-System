USE personalized_learning;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'admin') DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    student_name VARCHAR(150) NOT NULL,
    branch VARCHAR(100),
    semester INT,
    interests TEXT,
    preferred_difficulty INT DEFAULT 3,
    learning_level VARCHAR(50),
    academic_strength VARCHAR(50),
    engagement_strength VARCHAR(50),
    readiness_score DECIMAL(5,4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id VARCHAR(50) NOT NULL UNIQUE,
    course_name VARCHAR(200) NOT NULL,
    branch VARCHAR(100),
    semester INT,
    category VARCHAR(100),
    skills TEXT,
    prerequisites TEXT,
    difficulty INT,
    credits INT,
    course_level VARCHAR(50),
    is_core BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE student_courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    status ENUM('not_started', 'in_progress', 'completed') DEFAULT 'not_started',
    score DECIMAL(5,2),
    completed_at DATETIME NULL,

    FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE,

    UNIQUE(student_id, course_id)
);

CREATE TABLE student_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    skill_name VARCHAR(150) NOT NULL,
    skill_level DECIMAL(5,2) DEFAULT 0,
    source VARCHAR(100),

    FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    UNIQUE(student_id, skill_name)
);

CREATE TABLE recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    recommendation_rank INT NOT NULL,
    hybrid_score DECIMAL(8,6),
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE,

    UNIQUE(student_id, course_id)
);

CREATE TABLE skill_gaps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    skill_name VARCHAR(150) NOT NULL,
    current_level DECIMAL(5,2) DEFAULT 0,
    required_level DECIMAL(5,2) DEFAULT 0,
    gap_score DECIMAL(5,2) DEFAULT 0,
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',

    FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    UNIQUE(student_id, skill_name)
);

CREATE TABLE learning_paths (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    path_name VARCHAR(200) NOT NULL,
    description TEXT,
    total_courses INT DEFAULT 0,
    estimated_hours INT DEFAULT 0,
    status ENUM('active', 'completed', 'paused') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE
);

CREATE TABLE learning_path_courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    learning_path_id INT NOT NULL,
    course_id INT NOT NULL,
    sequence_number INT NOT NULL,
    status ENUM('locked', 'available', 'in_progress', 'completed')
        DEFAULT 'locked',

    FOREIGN KEY (learning_path_id)
        REFERENCES learning_paths(id)
        ON DELETE CASCADE,

    FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE
);

CREATE TABLE progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    progress_percent DECIMAL(5,2) DEFAULT 0,
    time_spent_minutes INT DEFAULT 0,
    last_activity DATETIME NULL,

    FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE,

    UNIQUE(student_id, course_id)
);

CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE
);

CREATE TABLE model_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(150) NOT NULL,
    precision_at_5 DECIMAL(8,6),
    recall_at_5 DECIMAL(8,6),
    ndcg_at_5 DECIMAL(8,6),
    students_evaluated INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);