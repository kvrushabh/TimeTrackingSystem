import React, { useState, useEffect } from 'react'
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, MenuItem, Grid
} from '@mui/material'
import dayjs from 'dayjs'
import api from '../api/axios'

const taskTypes = [
  'Internal Discussion', 'Development', 'Testing', 'Deployment',
  'Review', 'Break', 'Customer Interaction', 'Documentation'
]

const AddTaskModal = ({ open, handleClose, onTaskAdded }) => {
  const [form, setForm] = useState({
    user_id: null,
    date: dayjs().format('YYYY-MM-DD'),
    project_id: '',
    task_title: '',
    task_details: '',
    start_time: '',
    end_time: '',
    task_type: '',
    reviewer_id: null,
    is_backdated: false,
    is_approved: false,
    created_by: null
  })

  const [projects, setProjects] = useState([])

  const loadProjects = async () => {
    try {
      const res = await api.get('/projects/')
      setProjects(res.data)
    } catch (err) {
      console.error('Failed to load projects', err)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm({ ...form, [name]: value })
  }

  const handleSubmit = async () => {
    try {
      const user = JSON.parse(localStorage.getItem('user'))
      const today = dayjs().format('YYYY-MM-DD')

      const taskData = {
        ...form,
        user_id: user.id,
        created_by: user.id,
        is_backdated: form.date < today,
        status: form.date < today ? 'To Be Approved' : 'In Progress'
      }

      await api.post('/tasks/create', taskData)
      handleClose()
      onTaskAdded?.()
    } catch (err) {
      console.error('Failed to create task', err)
      alert('Error creating task')
    }
  }

  useEffect(() => {
    if (open) {
      loadProjects()
    }
  }, [open])

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="md">
      <DialogTitle>Add New Task</DialogTitle>
      <DialogContent>
        <Grid container spacing={2} mt={1}>
          <Grid item xs={12} sm={6}>
            <TextField
              label="Date" type="date" name="date" fullWidth size="small"
              value={form.date}
              onChange={handleChange}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              label="Project" name="project_id" fullWidth select size="small"
              value={form.project_id} onChange={handleChange}
            >
              {projects.map((proj) => (
                <MenuItem key={proj.id} value={proj.id}>{proj.project_name}</MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={12}>
            <TextField
              label="Task Title" name="task_title" fullWidth size="small"
              value={form.task_title} onChange={handleChange}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="Task Details" name="task_details" fullWidth size="small" multiline
              value={form.task_details} onChange={handleChange}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Start Time" type="datetime-local" name="start_time" fullWidth size="small"
              value={form.start_time} onChange={handleChange}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              label="End Time" type="datetime-local" name="end_time" fullWidth size="small"
              value={form.end_time} onChange={handleChange}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Task Type" name="task_type" fullWidth select size="small"
              value={form.task_type} onChange={handleChange}
            >
              {taskTypes.map((type) => (
                <MenuItem key={type} value={type}>{type}</MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              label="Reviewer (optional)" name="reviewer_id" fullWidth size="small"
              value={form.reviewer_id || ''} onChange={(e) => setForm({ ...form, reviewer_id: e.target.value })}
            />
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSubmit}>Add Task</Button>
      </DialogActions>
    </Dialog>
  )
}

export default AddTaskModal
