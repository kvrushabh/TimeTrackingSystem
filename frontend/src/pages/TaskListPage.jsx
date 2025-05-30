import React, { useEffect, useState } from 'react'
import { Box, Typography, CircularProgress } from '@mui/material'
import TaskTable from '../components/TaskTable.jsx'
import api from '../api/axios'

const TaskListPage = () => {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await api.post(`/tasks/list?page=1&page_size=10`, {})
        setTasks(res.data)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [])

  return (
    <Box p={2}>
      <Typography variant="h6" mb={2}>All Tasks</Typography>
      {loading ? <CircularProgress /> : <TaskTable tasks={tasks} />}
    </Box>
  )
}

export default TaskListPage
