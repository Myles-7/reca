import { Archive, ArchiveRestore, Pencil } from "lucide-react"
import type { FormEvent } from "react"

import { MutationError } from "@/components/reca-visual-refresh"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

import type {
  EditProjectDialogProps,
  ProjectLifecycleControlProps,
} from "./contracts"

import "./project-workspace.css"

export function ProjectLifecycleControl({
  action,
  pending,
  error,
  onAction,
}: ProjectLifecycleControlProps) {
  const restore = action === "restore"
  return (
    <div>
      <Button
        type="button"
        size="sm"
        variant="outline"
        aria-label={restore ? "Restore" : "Archive"}
        disabled={pending}
        onClick={onAction}
      >
        {restore ? (
          <ArchiveRestore aria-hidden="true" />
        ) : (
          <Archive aria-hidden="true" />
        )}
        {pending ? "正在提交" : restore ? "恢复项目" : "归档项目"}
      </Button>
      {error ? (
        <MutationError
          message={error.message}
          code={error.code}
          requestId={error.requestId}
        />
      ) : null}
    </div>
  )
}

export function EditProjectDialog({
  project,
  open,
  pending,
  error,
  onOpenChange,
  onUpdate,
}: EditProjectDialogProps) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    onUpdate({
      name: String(data.get("name") ?? "").trim(),
      description: String(data.get("description") ?? "").trim() || null,
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button
          type="button"
          size="sm"
          variant="outline"
          aria-label="Edit project"
        >
          <Pencil aria-hidden="true" />
          编辑项目
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form className="space-y-5" onSubmit={submit}>
          <DialogHeader>
            <DialogTitle>编辑项目</DialogTitle>
            <DialogDescription>
              更新仍使用当前项目版本执行冲突检测；本地输入不代表服务端已保存。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="edit-project-name">项目名称</Label>
            <Input
              id="edit-project-name"
              name="name"
              defaultValue={project.name}
              disabled={pending}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-project-description">项目说明</Label>
            <Input
              id="edit-project-description"
              name="description"
              defaultValue={project.description ?? ""}
              disabled={pending}
            />
          </div>
          {error ? (
            <MutationError
              message={error.message}
              code={error.code}
              requestId={error.requestId}
            />
          ) : null}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              disabled={pending}
              onClick={() => onOpenChange(false)}
            >
              取消
            </Button>
            <Button type="submit" disabled={pending}>
              {pending ? "正在保存" : "保存修改"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
