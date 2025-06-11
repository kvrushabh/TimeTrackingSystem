import React from 'react'
import { Tabs, Tab, Box } from '@mui/material'

const TaskTabs = ({ selectedTab, setSelectedTab }) => {
  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
      <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)} variant="fullWidth">
        <Tab label="Regular Tasks" value="regular" />
        <Tab label="Backdated Tasks" value="backdated" />
      </Tabs>
    </Box>
  )
}

export default TaskTabs
