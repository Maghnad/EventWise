"use client";

import { useState, useCallback } from "react";
import { useTimeline } from "./useTimeline";
import { TimelineForm } from "./TimelineForm";
import { Button, Card } from "@/shared/components";
import type {
  CreateTimelineTaskRequest,
  TaskStatus,
  TimelineTask,
  UpdateTimelineTaskRequest,
} from "@/shared/contracts";

/* ── Status colours ──────────────────────────────── */

const STATUS_COLORS: Record<TaskStatus, string> = {
  pending: "bg-gray-500/20 text-gray-300",
  in_progress: "bg-blue-500/20 text-blue-300",
  completed: "bg-emerald-500/20 text-emerald-300",
  delayed: "bg-red-500/20 text-red-300",
};

const STATUS_ICONS: Record<TaskStatus, string> = {
  pending: "○",
  in_progress: "◔",
  completed: "●",
  delayed: "◑",
};

/* ── Props ───────────────────────────────────────── */

export interface TimelinePageProps {
  eventId: string;
}

export function TimelinePage({ eventId }: TimelinePageProps): React.JSX.Element {
  const { overview, loading, error, refetch, createTask, updateTask, deleteTask } =
    useTimeline(eventId);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<TimelineTask | undefined>();
  const [submitting, setSubmitting] = useState(false);

  const openCreate = useCallback(() => {
    setEditing(undefined);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((task: TimelineTask) => {
    setEditing(task);
    setFormOpen(true);
  }, []);

  const handleSubmit = async (data: CreateTimelineTaskRequest) => {
    try {
      setSubmitting(true);
      if (editing) {
        await updateTask(editing.id, data as UpdateTimelineTaskRequest);
      } else {
        await createTask(data);
      }
      setFormOpen(false);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleStatus = async (task: TimelineTask) => {
    const next: TaskStatus = task.status === "completed" ? "pending" : "completed";
    await updateTask(task.id, { status: next });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  if (error || !overview) {
    return (
      <Card className="mx-auto mt-16 max-w-md text-center">
        <p className="text-red-400" role="alert">
          Failed to load timeline — {error?.message ?? "Unknown error"}
        </p>
        <Button className="mt-4" onClick={refetch}>
          Retry
        </Button>
      </Card>
    );
  }

  const pct =
    overview.total_tasks > 0
      ? Math.round((overview.completed_tasks / overview.total_tasks) * 100)
      : 0;

  return (
    <section aria-label="Timeline">
      {/* Summary */}
      <div className="mb-8 grid gap-4 sm:grid-cols-3">
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
      <div className="mb-8">
        <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-indigo-500 transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Tasks</h2>
        <Button onClick={openCreate} aria-label="Add timeline task">
          + Add Task
        </Button>
      </div>

      {/* Task list */}
      {overview.tasks.length === 0 ? (
        <Card className="py-16 text-center">
          <p className="mb-3 text-4xl">📅</p>
          <p className="text-gray-400">No tasks yet. Plan your first milestone!</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {overview.tasks
            .sort((a, b) => a.order_index - b.order_index)
            .map((task) => {
              const start = new Date(task.start_time).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              });

              return (
                <Card
                  key={task.id}
                  className="flex items-center gap-4 transition-all hover:border-indigo-500/30"
                >
                  {/* Toggle */}
                  <button
                    type="button"
                    onClick={() => toggleStatus(task)}
                    className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-sm transition-colors ${
                      task.status === "completed"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-white/5 text-gray-400 hover:bg-white/10"
                    }`}
                    aria-label={`Mark ${task.title} as ${task.status === "completed" ? "pending" : "completed"}`}
                  >
                    {STATUS_ICONS[task.status]}
                  </button>

                  {/* Content */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p
                        className={`truncate font-medium ${
                          task.status === "completed"
                            ? "text-gray-500 line-through"
                            : "text-white"
                        }`}
                      >
                        {task.title}
                      </p>
                      <span
                        className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUS_COLORS[task.status]}`}
                      >
                        {task.status.replace("_", " ")}
                      </span>
                    </div>
                    <div className="mt-1 flex gap-4 text-xs text-gray-500">
                      <span>{start}</span>
                      {task.category && <span>• {task.category}</span>}
                      {task.assigned_to && <span>• {task.assigned_to}</span>}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      className="px-2 py-1 text-xs"
                      onClick={() => openEdit(task)}
                      aria-label={`Edit ${task.title}`}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="danger"
                      className="px-2 py-1 text-xs"
                      onClick={() => deleteTask(task.id)}
                      aria-label={`Delete ${task.title}`}
                    >
                      ✕
                    </Button>
                  </div>
                </Card>
              );
            })}
        </div>
      )}

      <TimelineForm
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        initialData={editing}
        onSubmit={handleSubmit}
        submitting={submitting}
      />
    </section>
  );
}
