export interface User {
  id: string;
  email: string;
  name: string;
}

export interface Meeting {
  id: string;
  title: string;
  date?: string;
  created_at?: string;
  recordedAt?: string;
  duration?: number;
  status?: string;
  transcript?: string;
  summary?: string;
  notes?: string;
}

export interface ActionItem {
  id?: string;
  _id?: string;
  description: string;
  assignee?: string;
  due_date?: string;
  status: string;
  meeting_id?: string;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  speaker?: string;
}

export interface TranscriptResponse {
  id?: string;
  content?: string;
  timestampedSegments?: TranscriptSegment[];
}

export interface SummaryResponse {
  id?: string;
  summaryText?: string;
  keyPoints?: string[];
}

export interface ActionItemResponse {
  id?: string;
  _id?: string;
  description: string;
  status: string;
  dueDate?: string;
  meetingId?: string;
  assignee?: string;
}

export interface MeetingDetailResponse {
  id?: string;
  title: string;
  duration?: number;
  status: string;
  created_at?: string;
  recordedAt?: string;
  notes?: string;
  audioFilePath?: string;
  audio_url?: string;
  transcript?: TranscriptResponse;
  summary?: SummaryResponse;
  actionItems?: ActionItemResponse[];
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isLoading: boolean;
}

