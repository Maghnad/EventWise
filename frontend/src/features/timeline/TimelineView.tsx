"use client";

import React from "react";
import { Button, Card } from "@/shared/components";
import type { TimelineOverviewResponse, TimelineTask, TaskStatus } from "@/shared/contracts";

const STATUS_COLORS: Record<TaskStatus, string> = {
  pending: "bg-gray-500/20 text-gray-300",
  in_progress: "bg-blue-500/20 text-blue-300",
  completed: "bg-emerald-500/20 text-emerald-300",
  delayed: "bg-red-500/20 text-red-300",
};

export interface TimelineViewProps {
  overview: TimelineOverviewResponse;
  onStatusToggle?: (task: TimelineTask) => void;
  onEditTask?: (task: TimelineTask) => void;
  onDeleteTask?: (taskId: string) => void;
  onAddTask?: () => void;
  className?: string;
}

export function TimelineView({
  overview,
  onStatusToggle,
  onEditTask,
  onDeleteTask,
  onAddTask,
  className = "",
}: TimelineViewProps): React.JSX.Element {
  const pct =
    overview.total_tasks > 0
      ? Math.round((overview.completed_tasks / overview.total_tasks) * 100)
      : 0;

  return (
    <section aria-label="Timeline Tasks View" className={`space-y-8 ${className}`}>
      {/* Summary */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Total Tasks</p>
          <p className="mt-1 text-2xl font-bold text-white">{overview.total_tasks}</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Completed</p>
          <p className="mt-1 text-2xl font-bold text-emerald-400">
            {overview.completed_tasks}
          </p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500">Progress</p>
          <p className="mt-1 text-2xl font-bold text-indigo-400">{pct}%</p>
        </Card>
      </div>

      {/* Progress bar */}
      <div>
        <div
          className="h-2 w-full overflow-hidden rounded-full bg-white/10"
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Timeline progress percentage"
        >
          <div
            className="h-full rounded-full bg-indigo-500 transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Header & Add Button */}
      {onAddTask && (
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">Production Tasks</h2>
          <Button onClick={onAddTask} aria-label="Add timeline task">
            + Add Task
          </Button>
        </div>
      )}

      {/* Task list */}
      {overview.tasks.length === 0 ? (
        <Card className="py-16 text-center">
          <p className="mb-3 text-4xl">📅</p>
          <p className="text-gray-400">No tasks on this timeline yet.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {overview.tasks.map((task) => (
            <Card
              key={task.id}
              className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 transition-colors hover:bg-white/[0.03]"
            >
              <div className="flex items-start gap-3">
                {onStatusToggle && (
                  <button
                    type="button"
                    onClick={() => onStatusToggle(task)}
                    className={`mt-1 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded border transition-colors ${
                      task.status === "completed"
                        ? "border-emerald-500 bg-emerald-500/20 text-emerald-400"
                        : "border-white/20 hover:border-white/40"
                    }`}
                    aria-label={`Toggle task status for ${task.title}`}
                  >
                    {task.status === "completed" ? "✓" : ""}
                  </button>
                )}

                <div>
                  <p
                    className={`font-medium ${
                      task.status === "completed"
                        ? "text-gray-400 line-through"
                        : "text-white"
                    }`}
                  >
                    {task.title}
                  </p>
                  {task.description && (
                    <p className="mt-0.5 text-xs text-gray-400">{task.description}</p>
                  )}
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                    <span className="rounded bg-white/5 px-2 py-0.5 text-gray-400">
                      {task.category}
                    </span>
                    <span>
                      {new Date(task.start_time).toLocaleDateString([], {
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                    {task.assigned_to && <span>• {task.assigned_to}</span>}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 self-end sm:self-center">
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${
                    STATUS_COLORS[task.status]
                  }`}
                >
                  {task.status.replace("_", " ")}
                </span>

                {onEditTask && (
                  <Button
                    variant="ghost"
                    className="px-2 py-1 text-xs"
                    onClick={() => onEditTask(task)}
                    aria-label={`Edit ${task.title}`}
                  >
                    Edit
                  </Button>
                )}

                {onDeleteTask && (
                  <Button
                    variant="danger"
                    className="px-2 py-1 text-xs"
                    onClick={() => onDeleteTask(task.id)}
                    aria-label={`Delete ${task.title}`}
                  >
                    ✕
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
