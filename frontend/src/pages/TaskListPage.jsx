import React, { useState } from 'react'
import { Box, Typography, Button } from '@mui/material'
import TaskTabs from '../components/TaskTabs'
import AddTaskModal from '../modals/AddTaskModal'
import TaskTable from '../components/TaskTable'

const TaskListPage = () => {
  const [selectedTab, setSelectedTab] = useState('regular')
  const [openModal, setOpenModal] = useState(false)

  const [reloadKey, setReloadKey] = useState(0)
  const handleReload = () => setReloadKey(prev => prev + 1)

  return (
    <Box p={2}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} flexWrap="wrap" gap={2}>
        <Typography variant="h6">
          {selectedTab === 'regular' ? 'Regular Tasks' : 'Backdated Tasks'}
        </Typography>
        <Button variant="contained" onClick={() => setOpenModal(true)}>Add Task</Button>
      </Box>

      <TaskTabs selectedTab={selectedTab} setSelectedTab={setSelectedTab} />

      <TaskTable isBackdatedTab={selectedTab === 'backdated'} key={reloadKey} />
      <AddTaskModal
        open={openModal}
        handleClose={() => setOpenModal(false)}
        onTaskAdded={handleReload}
        isBackdated={selectedTab === 'backdated'}
      />

    </Box>
  )
}

export default TaskListPage
