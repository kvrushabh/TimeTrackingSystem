import React, { useState, useEffect } from 'react';
import {
  Modal, Box, Typography, TextField, Button,
  FormControl, Select, MenuItem, InputLabel, Alert
} from '@mui/material';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import { DateTime } from 'luxon';
import api from '../api/axios';
import { jwtDecode } from 'jwt-decode';

dayjs.extend(utc);

const taskTypes = [
  'Internal Discussion', 'Development', 'Testing', 'Deployment',
  'Review', 'Break', 'Customer Interaction', 'Documentation'
];

const style = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '90%',
  maxWidth: 450,
  bgcolor: 'background.paper',
  borderRadius: 2,
  boxShadow: 24,
  p: 3,
  maxHeight: '90vh',
  overflowY: 'auto',
};

const AddTaskModal = ({ open, handleClose, onTaskAdded, isBackdated, isEdit = false, editTaskData = null }) => {
  const [form, setForm] = useState({});
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState('');

  const token = localStorage.getItem('token');
  const currentUser = token ? (() => {
    try {
      const decoded = jwtDecode(token);
      return { role: decoded.role, id: parseInt(decoded.sub) };
    } catch {
      return { role: '', id: null };
    }
  })() : { role: '', id: null };

  const requiredFields = [
    ...(isBackdated && ['Manager', 'Admin', 'Management'].includes(currentUser.role) ? ['user_id'] : []),
    'project_id', 'task_title', 'task_details',
    ...(isBackdated ? ['start_time', 'end_time'] : []),
    'task_type'
  ];

  useEffect(() => {
    if (open) {
      fetchInitialData();
      initializeForm();
    }
  }, [open, isBackdated, isEdit, editTaskData]);

  const fetchInitialData = async () => {
    const [projectRes, userRes, allUserRes] = await Promise.all([
      api.get('/projects/'),
      isBackdated ? api.get('/users/get-users') : Promise.resolve({ data: [] }),
      api.get('/users/')
    ]);
    setProjects(projectRes.data);
    if (isBackdated) setUsers(userRes.data);
    setAllUsers(allUserRes.data);
  };

  const initializeForm = () => {
    const now = dayjs();
    setApiError('');

    if (isEdit && editTaskData) {
      setForm({
        ...editTaskData,
        start_time: editTaskData.start_time ? dayjs(editTaskData.start_time) : null,
        end_time: editTaskData.end_time ? dayjs(editTaskData.end_time) : null,
        reviewer_id: editTaskData.reviewer_id || '',
        total_time_minutes: editTaskData.total_time_minutes || 0
      });
    } else {
      setForm({
        user_id: (isBackdated && ['Manager', 'Admin', 'Management'].includes(currentUser.role)) ? '' : currentUser.id,
        created_by: currentUser.id,
        is_backdated: isBackdated,
        is_approved: false,
        date: now.format('YYYY-MM-DD'),
        project_id: '',
        task_title: '',
        task_details: '',
        start_time: isBackdated ? null : null,
        end_time: null,
        task_type: '',
        reviewer_id: '',
        status: isBackdated ? 'To Be Approved' : 'In Progress',
        total_time_minutes: 0,
      });
    }

    setErrors({});
  };

  const calculateTotalTime = (start, end) => {
    if (!start || !end) return 0;
    const startDate = dayjs(start);
    const endDate = dayjs(end);
    return endDate.isBefore(startDate) ? 0 : endDate.diff(startDate, 'minute');
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    const updated = { ...form, [name]: value };
    setForm(updated);
    setErrors(prev => ({ ...prev, [name]: false }));
  };

  const handleTimeChange = (field, value) => {
    const updated = { ...form, [field]: value };
    if (isBackdated && updated.start_time && updated.end_time) {
      updated.total_time_minutes = calculateTotalTime(updated.start_time, updated.end_time);
    }
    setForm(updated);
  };

  const validateForm = () => {
    const newErrors = {};
    requiredFields.forEach(field => {
      if (!form[field]) newErrors[field] = true;
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    const nowUtc = DateTime.utc();

    const payload = {
      ...form,
      reviewer_id: form.reviewer_id || null,
      user_id: (isBackdated && ['Manager', 'Admin', 'Management'].includes(currentUser.role))
        ? Number(form.user_id)
        : currentUser.id,
      created_by: currentUser.id,
      project_id: Number(form.project_id),
      date: isBackdated
        ? DateTime.fromJSDate(form.start_time.toDate()).toUTC().toISODate()
        : nowUtc.toISODate(),
      start_time: isBackdated && form.start_time
        ? DateTime.fromJSDate(form.start_time.toDate()).toUTC().toISO()
        : nowUtc.toISO(),
      end_time: form.end_time ? DateTime.fromJSDate(form.end_time.toDate()).toUTC().toISO() : null,
      total_time_minutes: isBackdated ? form.total_time_minutes : 0,
      is_backdated: isBackdated,
      is_approved: false,
      status: isBackdated ? 'To Be Approved' : 'In Progress',
      task_type: form.task_type
    };

    try {
      if (isEdit && editTaskData?.id) {
        await api.put(`/tasks/${editTaskData.id}/edit`, payload);
      } else {
        await api.post('/tasks/create', payload);
      }
      handleClose();
      onTaskAdded?.();
    } catch (err) {
      console.error('Failed to save task', err);
      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        'Unknown error occurred while saving task.';
      setApiError(message);
    }
  };

  const requiredMark = (label, required) => required ? `${label} *` : label;

  return (
    <Modal open={open} onClose={handleClose}>
      <Box sx={style}>
        <Typography variant="h6" mb={2}>
          {isEdit ? 'Edit Task' : isBackdated ? 'Add Backdated Task' : 'Add Regular Task'}
        </Typography>

        {apiError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {apiError}
          </Alert>
        )}

        {isBackdated && ['Manager', 'Admin', 'Management'].includes(currentUser.role) && (
          <>
            <InputLabel>{requiredMark("User", true)}</InputLabel>
            <FormControl fullWidth size="small" sx={{ mb: 2 }} error={errors.user_id}>
              <Select name="user_id" value={form.user_id} onChange={handleChange}>
                <MenuItem value=""><em>Select User</em></MenuItem>
                {users.map(u => (
                  <MenuItem key={u.id} value={u.id}>{u.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </>
        )}

        <InputLabel>{requiredMark("Project", true)}</InputLabel>
        <FormControl fullWidth size="small" sx={{ mb: 2 }} error={errors.project_id}>
          <Select name="project_id" value={form.project_id} onChange={handleChange}>
            <MenuItem value=""><em>Select Project</em></MenuItem>
            {projects.map(p => (
              <MenuItem key={p.id} value={p.id}>{p.project_name}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <InputLabel>{requiredMark("Task Type", true)}</InputLabel>
        <FormControl fullWidth size="small" sx={{ mb: 2 }} error={errors.task_type}>
          <Select name="task_type" value={form.task_type} onChange={handleChange}>
            <MenuItem value=""><em>Select Task Type</em></MenuItem>
            {taskTypes.map(t => (
              <MenuItem key={t} value={t}>{t}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <InputLabel>{requiredMark("Task Title", true)}</InputLabel>
        <TextField fullWidth size="small" name="task_title" value={form.task_title} onChange={handleChange} error={errors.task_title} sx={{ mb: 2 }} />

        <InputLabel>{requiredMark("Task Details", true)}</InputLabel>
        <TextField fullWidth size="small" multiline name="task_details" value={form.task_details} onChange={handleChange} error={errors.task_details} sx={{ mb: 2 }} />

        {isBackdated && (
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <InputLabel>{requiredMark("Start Time", true)}</InputLabel>
              <DateTimePicker
                value={form.start_time}
                onChange={(val) => handleTimeChange('start_time', val)}
                sx={{ mb: 2 }}
                slotProps={{
                  textField: {
                    error: errors.start_time,
                    size: 'small',
                    fullWidth: true
                  }
                }}
                disableFuture
                shouldDisableDate={(date) => form.end_time && date.isAfter(form.end_time)}
              />
            <InputLabel>{requiredMark("End Time", true)}</InputLabel>
            <DateTimePicker
              value={form.end_time}
              onChange={(val) => handleTimeChange('end_time', val)}
              sx={{ mb: 2 }}
              slotProps={{
                textField: {
                  error: errors.end_time,
                  size: 'small',
                  fullWidth: true
                }
              }}
              disableFuture
              shouldDisableDate={(date) =>
                form.start_time && dayjs(date).isBefore(dayjs(form.start_time), 'day')
              }
              shouldDisableTime={(timeValue, clockType) => {
                if (form.start_time && clockType === 'minutes') {
                  const minEndTime = dayjs(form.start_time).add(1, 'minute');
                  return dayjs(form.end_time)
                    .set(clockType, timeValue)
                    .isBefore(minEndTime);
                }
                return false;
              }}
            />
          </LocalizationProvider>
        )}

        <InputLabel>Reviewer (optional)</InputLabel>
        <FormControl fullWidth size="small" sx={{ mb: 2 }}>
          <Select name="reviewer_id" value={form.reviewer_id} onChange={handleChange}>
            <MenuItem value=""><em>Select Reviewer</em></MenuItem>
            {allUsers.map(u => (
              <MenuItem key={u.id} value={u.id}>{u.name} ({u.role})</MenuItem>
            ))}
          </Select>
        </FormControl>

        {isBackdated && (
          <>
            <InputLabel>Total Time (minutes)</InputLabel>
            <TextField
              fullWidth size="small"
              value={form.total_time_minutes}
              InputProps={{ readOnly: true }}
              sx={{ mb: 2 }}
            />
          </>
        )}

        <Box display="flex" justifyContent="flex-end" gap={2} flexWrap="wrap">
          <Button variant="outlined" fullWidth onClick={handleClose}>Cancel</Button>
          <Button variant="contained" fullWidth onClick={handleSubmit}>
            {isEdit ? 'Edit Task' : 'Add Task'}
          </Button>
        </Box>
      </Box>
    </Modal>
  );
};

export default AddTaskModal;
