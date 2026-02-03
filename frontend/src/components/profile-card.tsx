"use client";

import type { ProfileVersion } from "@/types/profile";

interface ProfileCardProps {
  profile: ProfileVersion;
  userName?: string;
}

export default function ProfileCard({ profile, userName }: ProfileCardProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-bold text-gray-900">
          {userName || "Unknown"}
        </h2>
        {profile.headline && (
          <p className="mt-1 text-gray-600">{profile.headline}</p>
        )}
        {profile.summary && (
          <p className="mt-4 text-sm text-gray-700 whitespace-pre-line">
            {profile.summary}
          </p>
        )}
      </div>

      {/* Experience */}
      {profile.experience.length > 0 && (
        <Section title="Experience">
          {profile.experience.map((exp, i) => (
            <div key={i} className="border-b border-gray-100 pb-4 last:border-0 last:pb-0">
              <h4 className="font-medium text-gray-900">{exp.title}</h4>
              <p className="text-sm text-gray-600">{exp.company}</p>
              {exp.start_date && (
                <p className="text-xs text-gray-500">
                  {exp.start_date} - {exp.end_date || "Present"}
                  {exp.location && ` · ${exp.location}`}
                </p>
              )}
              {exp.description && (
                <p className="mt-2 text-sm text-gray-700 whitespace-pre-line">
                  {exp.description}
                </p>
              )}
            </div>
          ))}
        </Section>
      )}

      {/* Education */}
      {profile.education.length > 0 && (
        <Section title="Education">
          {profile.education.map((edu, i) => (
            <div key={i} className="border-b border-gray-100 pb-4 last:border-0 last:pb-0">
              <h4 className="font-medium text-gray-900">{edu.school}</h4>
              {edu.degree && (
                <p className="text-sm text-gray-600">
                  {edu.degree}
                  {edu.field && `, ${edu.field}`}
                </p>
              )}
              {edu.start_date && (
                <p className="text-xs text-gray-500">
                  {edu.start_date} - {edu.end_date || ""}
                </p>
              )}
            </div>
          ))}
        </Section>
      )}

      {/* Skills */}
      {profile.skills.length > 0 && (
        <Section title="Skills">
          <div className="flex flex-wrap gap-2">
            {profile.skills.map((skill, i) => (
              <span
                key={i}
                className="rounded-full bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700"
              >
                {skill}
              </span>
            ))}
          </div>
        </Section>
      )}

      {/* Languages */}
      {profile.languages.length > 0 && (
        <Section title="Languages">
          {profile.languages.map((lang, i) => (
            <span key={i} className="text-sm text-gray-700">
              {lang.language}
              {lang.proficiency && ` (${lang.proficiency})`}
              {i < profile.languages.length - 1 && " · "}
            </span>
          ))}
        </Section>
      )}

      {/* Certifications */}
      {profile.certifications.length > 0 && (
        <Section title="Certifications">
          {profile.certifications.map((cert, i) => (
            <div key={i} className="text-sm">
              <span className="font-medium text-gray-900">{cert.name}</span>
              {cert.authority && (
                <span className="text-gray-600"> - {cert.authority}</span>
              )}
            </div>
          ))}
        </Section>
      )}
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>
      <div className="space-y-4">{children}</div>
    </div>
  );
}
