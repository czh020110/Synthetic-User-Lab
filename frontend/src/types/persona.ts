export type SkillLevel = 'newbie' | 'intermediate' | 'expert';
export type PatienceLevel = 'low' | 'medium' | 'high';
export type RiskPreference = 'low' | 'medium' | 'high';

export interface Persona {
  id: string;
  name: string;
  description: string;
  skill_level: SkillLevel;
  patience_level: PatienceLevel;
  risk_preference: RiskPreference;
  created_at: string;
  updated_at: string;
}

export interface PersonaCreate {
  name: string;
  description?: string;
  skill_level?: SkillLevel;
  patience_level?: PatienceLevel;
  risk_preference?: RiskPreference;
}

export interface PersonaUpdate {
  name?: string | null;
  description?: string | null;
  skill_level?: SkillLevel | null;
  patience_level?: PatienceLevel | null;
  risk_preference?: RiskPreference | null;
}
