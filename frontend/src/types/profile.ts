export interface ExperienceEntry {
  title: string;
  company: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  description?: string;
}

export interface EducationEntry {
  school: string;
  degree?: string;
  field?: string;
  location?: string;
  start_date?: string;
  end_date?: string;
}

export interface CertificationEntry {
  name: string;
  authority?: string;
  date?: string;
}

export interface LanguageEntry {
  language: string;
  proficiency?: string;
}

export interface PatentEntry {
  title: string;
  patent_number?: string;
  date?: string;
  description?: string;
}

export interface PublicationEntry {
  title: string;
  publisher?: string;
  date?: string;
  description?: string;
}

export interface ProfileVersion {
  id: string;
  user_id: string;
  version: number;
  source_type: string;
  source_filename?: string;
  headline?: string;
  summary?: string;
  experience: ExperienceEntry[];
  education: EducationEntry[];
  skills: string[];
  certifications: CertificationEntry[];
  languages: LanguageEntry[];
  patents: PatentEntry[];
  volunteer: any[];
  publications: PublicationEntry[];
  awards: any[];
  projects: any[];
  courses: any[];
  pdf_storage_key?: string;
  is_current: boolean;
  created_at: string;
  raw_parsed_data?: any;
}

export interface ProfileVersionSummary {
  id: string;
  version: number;
  source_type: string;
  source_filename?: string;
  headline?: string;
  is_current: boolean;
  created_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name?: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  created_at: string;
  updated_at: string;
}
