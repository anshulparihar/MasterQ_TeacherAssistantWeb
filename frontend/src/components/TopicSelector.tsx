'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronRight, ChevronDown } from 'lucide-react';
import { api } from '@/lib/api';

interface TopicData {
  topic_name: string;
  subtopics: string[];
  importance_score: number;
}

interface TopicSelectorProps {
  subjectId: string | null;
  selectedTopics: string[];
  selectedSubtopics: string[];
  onChange: (topics: string[], subtopics: string[]) => void;
}

export function TopicSelector({ subjectId, selectedTopics, selectedSubtopics, onChange }: TopicSelectorProps) {
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set());

  const { data: topics = [], isLoading } = useQuery<TopicData[]>({
    queryKey: ['topics', subjectId],
    queryFn: async () => {
      const res = await api.get(`/topics/by-subject?subject_id=${subjectId}`);
      return res.data;
    },
    enabled: !!subjectId,
  });

  // Automatically expand first 3 topics when loaded
  useEffect(() => {
    if (topics.length > 0 && expandedTopics.size === 0) {
      const initialExpanded = new Set(topics.slice(0, 3).map(t => t.topic_name));
      setExpandedTopics(initialExpanded);
    }
  }, [topics]);

  const toggleExpand = (topicName: string) => {
    const next = new Set(expandedTopics);
    if (next.has(topicName)) {
      next.delete(topicName);
    } else {
      next.add(topicName);
    }
    setExpandedTopics(next);
  };

  const handleTopicCheck = (topicName: string, subtopics: string[], checked: boolean) => {
    if (checked) {
      // Add topic, remove any of its subtopics from selectedSubtopics
      onChange([...selectedTopics, topicName], selectedSubtopics.filter(st => !subtopics.includes(st)));
    } else {
      // Remove topic
      onChange(selectedTopics.filter(t => t !== topicName), selectedSubtopics);
    }
  };

  const handleSubtopicCheck = (topicName: string, subtopic: string, allSubtopics: string[], checked: boolean) => {
    if (checked) {
      const newSubtopics = [...selectedSubtopics, subtopic];
      // Check if all subtopics are now selected
      const allSelected = allSubtopics.every(st => newSubtopics.includes(st));
      if (allSelected) {
        onChange([...selectedTopics, topicName], newSubtopics.filter(st => !allSubtopics.includes(st)));
      } else {
        onChange(selectedTopics, newSubtopics);
      }
    } else {
      // If the topic was selected, demote to subtopics minus the unchecked one
      if (selectedTopics.includes(topicName)) {
        onChange(
          selectedTopics.filter(t => t !== topicName),
          [...selectedSubtopics, ...allSubtopics.filter(st => st !== subtopic)]
        );
      } else {
        onChange(selectedTopics, selectedSubtopics.filter(st => st !== subtopic));
      }
    }
  };

  if (!subjectId) {
    return (
      <div className="space-y-4 border rounded-xl p-5 bg-card shadow-sm opacity-50 pointer-events-none">
        <h3 className="font-semibold text-sm border-b pb-3">Topics & Subtopics</h3>
        <p className="text-sm text-muted-foreground text-center py-4">Select a subject first</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 border rounded-xl p-5 bg-card shadow-sm">
      <div className="flex justify-between items-center border-b pb-3">
        <div>
          <h3 className="font-semibold text-sm">Topics & Subtopics</h3>
          <p className="text-xs text-muted-foreground mt-1">If none selected: all topics used</p>
        </div>
        <button 
          type="button" 
          onClick={() => onChange([], [])}
          className="text-xs text-primary hover:underline"
        >
          Clear
        </button>
      </div>

      {isLoading ? (
        <div className="text-sm text-muted-foreground animate-pulse p-4 text-center">Loading topics...</div>
      ) : topics.length === 0 ? (
        <div className="text-sm text-muted-foreground text-center p-4">No topics found for this subject</div>
      ) : (
        <div className="max-h-80 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
          {topics.map((topic) => {
            const isTopicSelected = selectedTopics.includes(topic.topic_name);
            const isExpanded = expandedTopics.has(topic.topic_name);
            
            return (
              <div key={topic.topic_name} className="border rounded-md">
                <div className="flex items-center justify-between p-3 bg-muted/30 hover:bg-muted/50 transition-colors">
                  <div className="flex items-center gap-2 flex-1">
                    <button 
                      type="button" 
                      onClick={() => toggleExpand(topic.topic_name)}
                      className="p-1 hover:bg-muted rounded text-muted-foreground"
                    >
                      {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </button>
                    <span className="text-sm font-medium">{topic.topic_name}</span>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer text-xs font-medium">
                    <input 
                      type="checkbox"
                      checked={isTopicSelected}
                      onChange={(e) => handleTopicCheck(topic.topic_name, topic.subtopics, e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                    />
                    All
                  </label>
                </div>
                
                {isExpanded && (
                  <div className="p-3 pt-1 pl-11 space-y-2 bg-muted/10 border-t">
                    {topic.subtopics.map(subtopic => {
                      const isSubtopicSelected = isTopicSelected || selectedSubtopics.includes(subtopic);
                      return (
                        <label key={subtopic} className="flex items-center gap-3 cursor-pointer group">
                          <input 
                            type="checkbox"
                            checked={isSubtopicSelected}
                            onChange={(e) => handleSubtopicCheck(topic.topic_name, subtopic, topic.subtopics, e.target.checked)}
                            className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                          />
                          <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">
                            {subtopic}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="pt-3 border-t text-xs text-muted-foreground">
        {selectedTopics.length === 0 && selectedSubtopics.length === 0 ? (
          <p>Generating from all topics</p>
        ) : (
          <p>
            Generating from:{' '}
            {[...selectedTopics, ...selectedSubtopics].slice(0, 3).join(', ')}
            {[...selectedTopics, ...selectedSubtopics].length > 3 && ` (+${[...selectedTopics, ...selectedSubtopics].length - 3} more)`}
          </p>
        )}
      </div>
    </div>
  );
}
