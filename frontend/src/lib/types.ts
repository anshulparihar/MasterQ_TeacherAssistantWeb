export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface Document {
  id: string;
  filename: string;
  doc_type: 'admin' | 'user';
  user_id?: string | null;
  s3_key: string;
  created_at: string;
}

export interface Subject {
  id: string;
  name: string;
  description?: string;
}

export interface Topic {
  id: string;
  subject_id: string;
  name: string;
  description?: string;
}

export interface ExamType {
  id: string;
  name: string;
  description?: string;
}

export interface Question {
  id: string;
  text: string;
  type: 'mcq' | 'theory';
  options?: string[]; // For MCQ
  correct_answer?: string; // For MCQ
  model_answer?: string; // For theory
  difficulty: 'easy' | 'medium' | 'hard';
  topic_id: string;
  created_at: string;
}

export interface QuestionPaper {
  id: string;
  title: string;
  user_id: string;
  subject_id: string;
  exam_type_id: string;
  questions: Question[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  references?: string[];
  created_at: string;
}

// API Response Wrappers
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface QuestionGenerationRequest {
  subject_id: string;
  exam_type_id: string;
  academic_level: string | null;
  document_ids: string[];
  from_this_only: boolean;
  mcq_easy: number;
  mcq_medium: number;
  mcq_hard: number;
  theory_easy: number;
  theory_medium: number;
  theory_hard: number;
  selected_topics: string[];
  selected_subtopics: string[];
  topics: string[];
}
