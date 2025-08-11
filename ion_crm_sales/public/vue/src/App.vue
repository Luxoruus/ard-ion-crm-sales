<template>
  <div id="app" class="w-full min-h-dvh" :class="{ 'rtl': currentLanguage === 'ar' }">
    <!-- Loading Overlay -->
    <div v-if="isLoading" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 flex items-center space-x-3">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span>{{ t('loading') }}</span>
      </div>
    </div>

    <!-- Toast Notifications -->
    <div v-if="toast.show" :class="[
      'fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300',
      toast.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
    ]">
      {{ toast.message }}
    </div>

    <!-- Login Page -->
    <div v-if="!isAuthenticated"
      class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div class="bg-white rounded-xl shadow-xl p-8 w-full max-w-md">
        <div class="text-center mb-8">
          <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <h1 class="text-3xl font-bold text-gray-900 mb-2">{{ t('welcome') }}</h1>
          <p class="text-gray-600">{{ t('loginSubtitle') }}</p>
        </div>

        <form @submit.prevent="login" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('username') }}</label>
            <input v-model="loginForm.username" type="text" required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              :placeholder="t('enterUsername')" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('password') }}</label>
            <input v-model="loginForm.password" type="password" required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              :placeholder="t('enterPassword')" />
          </div>

          <button type="submit" :disabled="isLoading"
            class="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 font-medium">
            <span v-if="!isLoading">{{ t('login') }}</span>
            <div v-else class="flex items-center justify-center">
              <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              {{ t('loading') }}
            </div>
          </button>
        </form>

        <div class="mt-6 text-center">
          <button @click="toggleLanguage"
            class="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors">
            {{ currentLanguage === 'en' ? 'العربية' : 'English' }}
          </button>
        </div>

        <!-- Demo credentials hint -->
        <div class="mt-6 p-4 bg-blue-50 rounded-lg">
          <p class="text-sm text-blue-800 text-center">
            <strong>Demo:</strong> Enter any username and password to login
          </p>
        </div>
      </div>
    </div>

    <!-- Main Application -->
    <div v-else class="min-h-screen bg-gray-50">
      <!-- Header -->
      <header class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex justify-between items-center h-16">
            <div class="flex items-center space-x-4">
              <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <h1 class="text-xl font-semibold text-gray-900">{{ t('surveyApp') }}</h1>
              <span class="text-sm text-gray-500">{{ t('welcome') }}, {{ currentUser?.full_name }}</span>
            </div>
            <div class="flex items-center space-x-4">
              <button @click="toggleLanguage"
                class="px-3 py-1 text-sm bg-gray-100 rounded-md hover:bg-gray-200 transition-colors">
                {{ currentLanguage === 'en' ? 'العربية' : 'English' }}
              </button>
              <button @click="logout"
                class="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors">
                {{ t('logout') }}
              </button>
            </div>
          </div>
        </div>
      </header>

      <!-- Navigation Tabs -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div class="border-b border-gray-200">
          <nav class="-mb-px flex space-x-8">
            <button @click="activeTab = 'fill-survey'" :class="[
              'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === 'fill-survey'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]">
              <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z">
                </path>
              </svg>
              {{ t('fillSurvey') }}
            </button>
            <button @click="activeTab = 'my-surveys'" :class="[
              'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === 'my-surveys'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]">
              <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2">
                </path>
              </svg>
              {{ t('mySurveys') }}
            </button>
          </nav>
        </div>
      </div>

      <!-- Fill Survey Tab -->
      <div v-if="activeTab === 'fill-survey'" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="bg-white rounded-lg shadow-sm p-6">
          <!-- Opportunity Selection -->
          <div v-if="!selectedOpportunity" class="space-y-6">
            <div class="text-center mb-8">
              <h2 class="text-2xl font-bold text-gray-900 mb-2">{{ t('selectOpportunity') }}</h2>
              <p class="text-gray-600">Choose an opportunity to begin the technical assessment survey</p>
              <p class="text-sm text-blue-600 mt-2">Only showing opportunities in "Surveying" state without an assigned surveyor
              </p>
            </div>

            <div class="flex items-end justify-between">
              <div class="flex-1">
                <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('searchOpportunities') }}</label>
                <div class="relative">
                  <input v-model="opportunitySearch" type="text"
                    class="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 transition-all"
                    :placeholder="t('searchPlaceholder')" />
                  <svg class="w-5 h-5 text-gray-400 absolute left-3 top-3.5" fill="none" stroke="currentColor"
                    viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                  </svg>
                </div>
              </div>
              <button @click="fetchOpportunities" :disabled="isLoading"
                class="ml-4 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                  </path>
                </svg>
                {{ t('refresh') }}
              </button>
            </div>

            <div v-if="filteredOpportunities.length === 0 && !isLoading" class="text-center py-12">
              <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2">
                </path>
              </svg>
              <p class="text-gray-500 text-lg font-medium">{{ t('noAvailableOpportunities') }}</p>
              <p class="text-gray-400 mt-2">All opportunities in the "Surveying" workflow state have already been assigned to a surveyor</p>
            </div>

            <div v-else class="grid gap-4">
              <div v-for="opportunity in filteredOpportunities" :key="opportunity.name"
                @click="selectOpportunity(opportunity)"
                class="p-6 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 cursor-pointer transition-all duration-200 hover:shadow-md">
                <div class="flex justify-between items-start">
                  <div class="flex-1">
                    <h3 class="font-semibold text-gray-900 text-lg mb-2">{{ opportunity.title }}</h3>
                    <div class="flex items-center space-x-4 text-sm text-gray-600">
                      <span class="flex items-center">
                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h4M9 7h6m-6 4h6m-6 4h6">
                          </path>
                        </svg>
                        {{ opportunity.doctype }}
                      </span>
                      <span class="flex items-center">
                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                        </svg>
                        {{ opportunity.customer_name }}
                      </span>
                    </div>
                  </div>
                  <div class="flex flex-col items-end space-y-2">
                    <span :class="[
                      'px-3 py-1 text-xs font-medium rounded-full',
                      opportunity.status === 'Open' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                    ]">
                      {{ opportunity.status }}
                    </span>
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Survey Form -->
          <div v-else class="space-y-6">
            <!-- Survey Header -->
            <div class="flex items-center justify-between pb-6 border-b">
              <div>
                <h2 class="text-2xl font-bold text-gray-900">{{ selectedOpportunity.title }}</h2>
                <p class="text-gray-600 mt-1 flex items-center">
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h4M9 7h6m-6 4h6m-6 4h6">
                    </path>
                  </svg>
                  {{ selectedOpportunity.doctype }}
                </p>
              </div>
              <button @click="selectedOpportunity = null"
                class="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors flex items-center">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18">
                  </path>
                </svg>
                {{ t('back') }}
              </button>
            </div>

            <!-- Survey Template Selection -->
            <div class="bg-blue-50 rounded-lg p-4">
              <div class="flex items-center justify-between mb-3">
                <h3 class="text-lg font-medium text-gray-900 flex items-center">
                  <svg class="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2">
                    </path>
                  </svg>
                  {{ t('selectSurveyTemplate') }}
                </h3>
                <span v-if="currentSurveyTemplate" class="text-sm text-green-600 font-medium">{{ t('templateSelected') }}</span>
              </div>
              <select v-model="selectedTemplateId" @click="fetchSurveyTemplates" @change="selectSurveyTemplate(selectedTemplateId)"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="">{{ t('chooseTemplate') }}</option>
                <option v-for="template in surveyTemplates" :key="template.name" :value="template.name">
                  {{ template.template_name }}
                </option>
              </select>
              <p class="text-sm text-gray-600 mt-2">{{ t('templateSelectionHint') }}</p>
            </div>

            <!-- Progress Bar -->
            <div v-if="currentSurveyTemplate" class="bg-gray-100 rounded-lg p-4">
              <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-medium text-gray-700">{{ t('progress') }}</span>
                <span class="text-sm font-medium text-blue-600">{{ Math.round(surveyProgress) }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-3">
                <div
                  class="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
                  :style="{ width: `${surveyProgress}%` }"></div>
              </div>
            </div>

            <!-- Survey Questions -->
            <div v-if="currentSurveyTemplate" class="space-y-8">
              <div v-for="(question, index) in currentSurveyTemplate?.questions" :key="question.name"
                class="p-6 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors">
                <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-start">
                  <span
                    class="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold mr-3 mt-0.5">
                    {{ index + 1 }}
                  </span>
                  <span>
                    {{ question.question }}
                    <span v-if="question.required" class="text-red-500 ml-1">*</span>
                  </span>
                </h3>
                
                <!-- Field Description -->
                <div v-if="question.description" class="ml-11 mb-3">
                  <p class="text-sm text-gray-600 italic">{{ question.description }}</p>
                </div>

                <!-- Text Input -->
                <div v-if="question.question_type === 'Text'" class="ml-11">
                  <textarea 
                    v-model="surveyAnswers[question.name]"
                    class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    rows="4" 
                    :placeholder="question.default_value || t('enterAnswer')"
                    @focus="initializeFieldValue(question)"></textarea>
                </div>

                <!-- Rating -->
                <div v-else-if="question.question_type === 'Rating'" class="ml-11">
                  <div class="flex space-x-2">
                    <button v-for="rating in 5" :key="rating" 
                      @click="surveyAnswers[question.name] = rating" 
                      @mouseenter="initializeFieldValue(question)"
                      :class="[
                      'w-12 h-12 rounded-full border-2 transition-all duration-200 flex items-center justify-center text-xl',
                      surveyAnswers[question.name] >= rating
                        ? 'bg-yellow-400 border-yellow-400 text-white shadow-md transform scale-110'
                        : 'border-gray-300 hover:border-yellow-400 hover:bg-yellow-50 text-gray-400'
                    ]">
                      ★
                    </button>
                  </div>
                  <p class="text-sm text-gray-500 mt-2">Click to rate from 1 to 5 stars</p>
                </div>

                <!-- Yes/No -->
                <div v-else-if="question.question_type === 'Yes/No'" class="ml-11">
                  <div class="flex space-x-4">
                    <button @click="surveyAnswers[question.name] = 'Yes'" 
                      @mouseenter="initializeFieldValue(question)"
                      :class="[
                      'px-8 py-3 rounded-lg border-2 transition-all duration-200 font-medium flex items-center',
                      surveyAnswers[question.name] === 'Yes'
                        ? 'bg-green-500 border-green-500 text-white shadow-md'
                        : 'border-gray-300 hover:border-green-500 hover:bg-green-50 text-gray-700'
                    ]">
                      <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                      </svg>
                      {{ t('yes') }}
                    </button>
                    <button @click="surveyAnswers[question.name] = 'No'" :class="[
                      'px-8 py-3 rounded-lg border-2 transition-all duration-200 font-medium flex items-center',
                      surveyAnswers[question.name] === 'No'
                        ? 'bg-red-500 border-red-500 text-white shadow-md'
                        : 'border-gray-300 hover:border-red-500 hover:bg-red-50 text-gray-700'
                    ]">
                      <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12">
                        </path>
                      </svg>
                      {{ t('no') }}
                    </button>
                  </div>
                </div>

                <!-- Multi-choice -->
                <div v-else-if="question.question_type === 'Multi-choice'" class="ml-11 space-y-3">
                  <div v-for="option in question.options" :key="option"
                    class="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                    <input :id="`${question.name}-${option}`" 
                      v-model="surveyAnswers[question.name]" 
                      :value="option"
                      type="radio" 
                      class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                      @focus="initializeFieldValue(question)" />
                    <label :for="`${question.name}-${option}`"
                      class="ml-3 block text-sm font-medium text-gray-700 cursor-pointer flex-1">
                      {{ option }}
                    </label>
                  </div>
                </div>

                <!-- Validation Error -->
                <div v-if="validationErrors[question.name]" class="ml-11 mt-3">
                  <p class="text-sm text-red-600 flex items-center">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    {{ validationErrors[question.name] }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex justify-between pt-6 border-t bg-gray-50 -mx-6 -mb-6 px-6 py-6 rounded-b-lg">
              <button @click="saveDraft" :disabled="isLoading"
                class="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50 flex items-center font-medium">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12">
                  </path>
                </svg>
                {{ t('saveDraft') }}
              </button>
              <button @click="submitSurvey" :disabled="isLoading"
                class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center font-medium">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                </svg>
                {{ t('submitSurvey') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- My Surveys Tab -->
      <div v-if="activeTab === 'my-surveys'" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="bg-white rounded-lg shadow-sm p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-bold text-gray-900 flex items-center">
              <svg class="w-6 h-6 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2">
                </path>
              </svg>
              {{ t('mySurveys') }}
            </h2>
            <div class="flex items-center space-x-4">
              <div class="text-sm text-gray-500">
                {{ filteredSurveyResponses.length }} {{ filteredSurveyResponses.length === 1 ? 'survey' : 'surveys' }} assigned to you
              </div>
              <button @click="fetchSurveyResponses" :disabled="isLoading"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                  </path>
                </svg>
                {{ t('refresh') }}
              </button>
            </div>
          </div>

          <!-- Filters -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Doctype</label>
              <select v-model="filters.doctype"
                class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="">{{ t('allDoctypes') }}</option>
                <option value="Opportunity">Opportunity</option>
                <option value="Opportunity Hotels">Opportunity Hotels</option>
                <option value="Opportunity SM">Opportunity SM</option>
                <option value="Opportunity Tenders">Opportunity Tenders</option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Status</label>
              <select v-model="filters.status"
                class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="">{{ t('allStatuses') }}</option>
                <option value="In Progress">{{ t('inProgress') }}</option>
                <option value="Submitted">{{ t('submitted') }}</option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">From Date</label>
              <input v-model="filters.dateFrom" type="date"
                class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">To Date</label>
              <input v-model="filters.dateTo" type="date"
                class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            </div>
          </div>

          <!-- Survey Responses List -->
          <div class="space-y-4">
            <div v-for="response in filteredSurveyResponses" :key="response.name"
              class="p-6 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all duration-200">
              <div class="flex justify-between items-start">
                <div class="flex-1">
                  <h3 class="font-semibold text-gray-900 text-lg mb-2">{{ response.title }}</h3>
                  <div class="space-y-1 text-sm text-gray-600">
                    <p class="flex items-center">
                      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h4M9 7h6m-6 4h6m-6 4h6">
                        </path>
                      </svg>
                      {{ response.doctype }}
                    </p>
                    <p class="flex items-center">
                      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                      </svg>
                      {{ response.customer_name }}
                    </p>
                    <p class="flex items-center">
                      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 4v10m6-10v10"></path>
                      </svg>
                      {{ t('assigned') }}: {{ formatDate(response.creation) }}
                    </p>
                  </div>
                </div>
                <div class="flex items-center space-x-3">
                  <span :class="[
                    'px-3 py-1 text-xs font-medium rounded-full',
                    response.status === 'In Progress'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-green-100 text-green-800'
                  ]">
                    {{ response.status === 'In Progress' ? t('inProgress') : t('submitted') }}
                  </span>
                  <button @click="viewSurveyResponse(response)"
                    class="px-4 py-2 text-sm bg-blue-100 text-blue-800 rounded-md hover:bg-blue-200 transition-colors flex items-center">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z">
                      </path>
                    </svg>
                    {{ response.status === 'In Progress' ? t('continue') : t('view') }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="filteredSurveyResponses.length === 0" class="text-center py-12">
            <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2">
              </path>
            </svg>
            <p class="text-gray-500 text-lg font-medium">{{ t('noSurveys') }}</p>
            <p class="text-gray-400 mt-2">No opportunities have been assigned to you yet</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'

export default {
  name: 'TechnicalAssessmentSurveyApp',
  setup() {

    // const tailwindScript = document.createElement('script')
    // tailwindScript.setAttribute('src', 'https://cdn.tailwindcss.com')
    // document.head.appendChild(tailwindScript)


    // Reactive state
    const isLoading = ref(false)
    const isAuthenticated = ref(false)
    const currentUser = ref(null)
    const activeTab = ref('fill-survey')
    const currentLanguage = ref('en')

    // Toast notifications
    const toast = reactive({
      show: false,
      message: '',
      type: 'success'
    })

    // Login form
    const loginForm = reactive({
      username: '',
      password: ''
    })

    // Opportunities and surveys
    const opportunities = ref([])
    const selectedOpportunity = ref(null)
    const currentSurveyTemplate = ref(null)
    const surveyTemplates = ref([])
    const selectedTemplateId = ref(null)
    const surveyAnswers = reactive({})
    const validationErrors = reactive({})
    const opportunitySearch = ref('')
    const surveyResponses = ref([])

    // Filters for My Surveys
    const filters = reactive({
      doctype: '',
      status: '',
      dateFrom: '',
      dateTo: ''
    })

    // Auto-save interval
    let autoSaveInterval = null

    // Translations
    const translations = {
      en: {
        welcome: 'Welcome',
        loginSubtitle: 'Technical Assessment Survey System',
        username: 'Username',
        password: 'Password',
        enterUsername: 'Enter your username',
        enterPassword: 'Enter your password',
        login: 'Login',
        logout: 'Logout',
        loading: 'Loading...',
        surveyApp: 'Survey Application',
        fillSurvey: 'Fill Survey',
        mySurveys: 'My Surveys',
        selectOpportunity: 'Select an Opportunity',
        searchOpportunities: 'Search Opportunities',
        searchPlaceholder: 'Search by name or customer...',
        customer: 'Customer',
        back: 'Back',
        progress: 'Progress',
        enterAnswer: 'Enter your answer...',
        yes: 'Yes',
        no: 'No',
        saveDraft: 'Save Draft',
        submitSurvey: 'Submit Survey',
        allDoctypes: 'All Doctypes',
        allStatuses: 'All Statuses',
        draft: 'Draft',
        submitted: 'Submitted',
        inProgress: 'In Progress',
        edit: 'Edit',
        view: 'View',
        continue: 'Continue',
        assigned: 'Assigned',
        noSurveys: 'No surveys found',
        noAvailableOpportunities: 'No available opportunities',
        refresh: 'Refresh',
        loginError: 'Invalid username or password',
        selectSurveyTemplate: 'Select Survey Template',
        templateSelected: 'Template Selected',
        chooseTemplate: 'Choose a template...',
        templateSelectionHint: 'Please select a survey template to begin the assessment',
        saveSuccess: 'Survey saved successfully',
        submitSuccess: 'Survey submitted successfully',
        validationError: 'This field is required',
        saveSuccess: 'Survey saved successfully',
        submitSuccess: 'Survey submitted successfully',
        validationError: 'This field is required',
        selectSurveyTemplate: 'Select Survey Template',
        templateSelected: 'Template Selected',
        chooseTemplate: 'Choose a survey template...',
        templateSelectionHint: 'Please select a survey template to begin the assessment'
      },
      ar: {
        welcome: 'مرحباً',
        loginSubtitle: 'نظام استطلاع التقييم الفني',
        username: 'اسم المستخدم',
        password: 'كلمة المرور',
        enterUsername: 'أدخل اسم المستخدم',
        enterPassword: 'أدخل كلمة المرور',
        login: 'تسجيل الدخول',
        logout: 'تسجيل الخروج',
        loading: 'جاري التحميل...',
        surveyApp: 'تطبيق الاستطلاع',
        fillSurvey: 'ملء الاستطلاع',
        mySurveys: 'استطلاعاتي',
        selectOpportunity: 'اختر فرصة',
        searchOpportunities: 'البحث في الفرص',
        searchPlaceholder: 'البحث بالاسم أو العميل...',
        customer: 'العميل',
        back: 'رجوع',
        progress: 'التقدم',
        enterAnswer: 'أدخل إجابتك...',
        yes: 'نعم',
        no: 'لا',
        saveDraft: 'حفظ مسودة',
        submitSurvey: 'إرسال الاستطلاع',
        allDoctypes: 'جميع الأنواع',
        allStatuses: 'جميع الحالات',
        draft: 'مسودة',
        submitted: 'مرسل',
        inProgress: 'قيد التقدم',
        edit: 'تعديل',
        view: 'عرض',
        continue: 'متابعة',
        assigned: 'مُعيَّن',
        noSurveys: 'لا توجد استطلاعات',
        noAvailableOpportunities: 'لا توجد فرص متاحة',
        refresh: 'تحديث',
        loginError: 'اسم المستخدم أو كلمة المرور غير صحيحة',
        saveSuccess: 'تم حفظ الاستطلاع بنجاح',
        submitSuccess: 'تم إرسال الاستطلاع بنجاح',
        validationError: 'هذا الحقل مطلوب',
        selectSurveyTemplate: 'اختر نموذج الاستطلاع',
        templateSelected: 'تم اختيار النموذج',
        chooseTemplate: 'اختر نموذج استطلاع...',
        templateSelectionHint: 'يرجى اختيار نموذج استطلاع لبدء التقييم'
      }
    }

    // Translation helper
    const t = (key) => translations[currentLanguage.value][key] || key

    // Computed properties
    const filteredOpportunities = computed(() => {
      if (!opportunitySearch.value) return opportunities.value
      const search = opportunitySearch.value.toLowerCase()
      return opportunities.value.filter(opp =>
        opp.title.toLowerCase().includes(search) ||
        opp.customer_name.toLowerCase().includes(search)
      )
    })

    const surveyProgress = computed(() => {
      if (!currentSurveyTemplate.value?.questions) return 0
      const totalQuestions = currentSurveyTemplate.value.questions.length
      
      // Count fields that have been meaningfully filled by the user
      const answeredQuestions = currentSurveyTemplate.value.questions.filter(question => {
        const answer = surveyAnswers[question.name]
        
        // Skip if no answer
        if (answer === null || answer === undefined || answer === '') return false
        
        // For checkbox fields, only count if explicitly set to true
        if (question.question_type === 'Yes/No' && typeof answer === 'boolean') {
          return answer !== false
        }
        
        // For numeric fields, only count if not zero (unless zero is meaningful)
        if (question.question_type === 'Text' && typeof answer === 'number') {
          return answer !== 0
        }
        
        // For select fields, check if it's not the default first option
        if (question.question_type === 'Multi-choice' && question.options) {
          return answer !== question.options[0]
        }
        
        // For other fields, check if it's not empty or default value
        return answer !== question.default_value && answer !== ''
      }).length
      
      return totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0
    })

    const filteredSurveyResponses = computed(() => {
      let filtered = surveyResponses.value

      if (filters.doctype) {
        filtered = filtered.filter(response => response.doctype === filters.doctype)
      }

      if (filters.status) {
        filtered = filtered.filter(response => response.status === filters.status)
      }

      if (filters.dateFrom) {
        filtered = filtered.filter(response => new Date(response.creation) >= new Date(filters.dateFrom))
      }

      if (filters.dateTo) {
        filtered = filtered.filter(response => new Date(response.creation) <= new Date(filters.dateTo))
      }

      return filtered
    })

    // Methods
    const showToast = (message, type = 'success') => {
      toast.message = message
      toast.type = type
      toast.show = true
      setTimeout(() => {
        toast.show = false
      }, 3000)
    }

    const toggleLanguage = () => {
      currentLanguage.value = currentLanguage.value === 'en' ? 'ar' : 'en'
      localStorage.setItem('language', currentLanguage.value)
    }

    async function checkLoggedIn() {
      try {
        // const ezgz = await fetch('/api/method/frappe.auth.get_csrf_token')
        // console.log(ezgz)
        const response = await fetch('/api/method/frappe.auth.get_logged_user', {
          credentials: 'include', // ensures cookies are sent
        });
        const data = await response.json();
        if (data.message) {
          // User is logged in, data.message is the username
          return { loggedIn: true, user: data.message };
        }
        // Not logged in
        return { loggedIn: false };
      } catch (err) {
        return { loggedIn: false };
      }
    }

    async function getUserRoles(username) {
      const resp = await fetch(`/api/resource/User/${username}`, {
        credentials: 'include', // critical for session!
      });
      const data = await resp.json();
      // Roles are in data.data.roles as an array of {role: "Pre-Sale"}, etc.
      return data.data.roles.map(r => r.role);
    }

    async function login() {
      isLoading.value = true
      try {
        const response = await fetch('/api/method/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            usr: loginForm.username,
            pwd: loginForm.password
          }),
          credentials: 'include' // important! sends/receives cookies
        });

        const data = await response.json();

        if (data.message === 'Logged In') {

          const roles = await getUserRoles(loginForm.username);

          if (roles.includes('Pre-Sale')) {
            // Success! Session cookie set, you can now call other APIs
            isAuthenticated.value = true
            currentUser.value = {
              name: loginForm.username,
              full_name: 'Technical Assessment User',
              roles: ['Technical Assessment']
            }
            await Promise.all([fetchOpportunities(), fetchSurveyResponses()])
            showToast('Login successful!')

            return { success: true };
          } else {
            await fetch('/api/method/logout', { method: 'POST', credentials: 'include' });
            console.log('User does not have Pre-Sale role, logging out');
            let error = new Error('Access denied: You do not have the Pre-Sale role.');
            error.code = 401
            throw error
          }

        } else {
          // Failed login
          return { success: false, error: data.message || 'Login failed' };
        }
      } catch (err) {
        if (err.code === 401) {
          showToast('Unauthorized access', 'error')
        } else {
          showToast(t('loginError'), 'error')
        }
        return { success: false, error: err.message };
      } finally {
        isLoading.value = false
      }
    }

    // const login = async () => {
    //   isLoading.value = true
    //   try {
    //     // Simulate API call to Frappe
    //     await new Promise(resolve => setTimeout(resolve, 1500))


    //     // Mock successful login - accept any username/password for demo
    //     if (loginForm.username && loginForm.password) {
    //       isAuthenticated.value = true
    //       currentUser.value = {
    //         name: loginForm.username,
    //         full_name: 'Technical Assessment User',
    //         roles: ['Technical Assessment']
    //       }
    //       await fetchOpportunities()
    //       await fetchSurveyResponses()
    //       showToast('Login successful!')
    //     } else {
    //       throw new Error('Invalid credentials')
    //     }
    //   } catch (error) {
    //     showToast(t('loginError'), 'error')
    //   } finally {
    //     isLoading.value = false
    //   }
    // }

    const logout = async () => {
      await fetch('/api/method/logout', { method: 'POST', credentials: 'include' });
      isAuthenticated.value = false
      currentUser.value = null
      selectedOpportunity.value = null
      currentSurveyTemplate.value = null
      surveyTemplates.value = []
      selectedTemplateId.value = null
      Object.keys(surveyAnswers).forEach(key => delete surveyAnswers[key])
      if (autoSaveInterval) {
        clearInterval(autoSaveInterval)
      }
      showToast('Logged out successfully')
    }

    const fetchOpportunities = async () => {
      opportunities.value = [] // Clear existing opportunities

      const fields = encodeURIComponent(JSON.stringify(['name', 'customer_name', 'opportunity_from', 'title', 'status', 'workflow_state', 'custom_surveyor']));
      const filters = encodeURIComponent(JSON.stringify([
        ['workflow_state', '=', 'Surveying'],
        ['custom_surveyor', 'is', 'not set']
      ]));

      for (const oppType of ["Opportunity", "Opportunity Hotels", "Opportunity SM", "Opportunity Tenders"]) {
        try {
          const resp = await fetch(`/api/resource/${oppType}?fields=${fields}&filters=${filters}`, {
            credentials: 'include',
          });

          if (resp.ok) {
            const data = await resp.json();
            const filteredOpportunities = data.data
              .filter(opp =>
                opp.workflow_state === 'Surveying' &&
                (!opp.custom_surveyor || opp.custom_surveyor === null || opp.custom_surveyor === '')
              )
              .map(opp => ({ ...opp, doctype: oppType }));

            opportunities.value.push(...filteredOpportunities);
          }
        } catch (error) {
          console.error(`Error fetching ${oppType}:`, error);
        }
      }

      console.log('Filtered opportunities:', opportunities.value)
    }

    const fetchSurveyTemplates = async () => {
      try {
        const fields = encodeURIComponent(JSON.stringify(['name', 'template_name', 'fields']));
        const resp = await fetch(`/api/resource/Technical Survey Template?fields=${fields}&limit_page_length=0`, {
          credentials: 'include',
        });

        if (resp.ok) {
          const data = await resp.json();
          surveyTemplates.value = data.data || [];
          console.log('Fetched survey templates:', surveyTemplates.value);
        } else {
          throw new Error('Failed to fetch survey templates');
        }
      } catch (error) {
        console.error('Error fetching survey templates:', error);
        showToast('Error loading survey templates', 'error');
      }
    };

    const selectOpportunity = async (opportunity) => {
      // Show confirmation modal
      if (confirm(`Are you sure you want to survey "${opportunity.title}"? You will be assigned as the surveyor for this opportunity.`)) {
        isLoading.value = true
        try {
          // Assign current user as surveyor in ERPNext
          const response = await fetch(`/api/resource/${opportunity.doctype}/${opportunity.name}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'X-Frappe-CSRF-Token': window.csrf_token
            },
            credentials: 'include',
            body: JSON.stringify({
              custom_surveyor: currentUser.value.name
            })
          })

          if (!response.ok) {
            throw new Error('Failed to assign surveyor')
          }

          selectedOpportunity.value = opportunity
          await fetchSurveyTemplates()
          // Don't start auto-save yet - wait for template selection
          
          // Refresh opportunities list to remove the assigned opportunity
          await fetchOpportunities()

          showToast('You have been assigned as the surveyor for this opportunity')
        } catch (error) {
          showToast('Error assigning surveyor: ' + error.message, 'error')
        } finally {
          isLoading.value = false
        }
      }
    }

    const selectSurveyTemplate = async (templateId) => {
      if (!templateId) return;
      
      isLoading.value = true;
      try {
        // Fetch the complete template data including child table fields
        const resp = await fetch(`/api/resource/Technical Survey Template/${templateId}`, {
          credentials: 'include',
        });
        
        if (!resp.ok) {
          throw new Error('Failed to fetch template details');
        }
        
        const data = await resp.json();
        const template = data.data;
        
        if (!template) {
          throw new Error('Template not found');
        }
        
        selectedTemplateId.value = templateId;
        
        // Check if fields exist and is an array
        const templateFields = template.fields || [];
        console.log('Template fields:', templateFields);
        
        // Convert template fields to survey questions format
        currentSurveyTemplate.value = {
          title: template.template_name,
          questions: templateFields.map(field => ({
            name: field.field_name,
            question: field.field_label,
            description: field.description || '',
            question_type: mapFieldTypeToQuestionType(field.field_type),
            required: field.is_mandatory === 1,
            options: field.options ? field.options.split('\n').filter(opt => opt.trim() !== '') : undefined
          }))
        };
        
        // Initialize survey answers based on template fields
        surveyAnswers.value = {};
        templateFields.forEach(field => {
          surveyAnswers.value[field.field_name] = initializeFieldValue(field);
        });
        
        // Start auto-save now that template is selected
        startAutoSave();
        activeTab.value = 'fill-survey';
        
        showToast(`Template "${template.template_name}" selected successfully`);
      } catch (error) {
        showToast('Error selecting template: ' + error.message, 'error');
      } finally {
        isLoading.value = false;
      }
    };

    const mapFieldTypeToQuestionType = (fieldType) => {
      const typeMap = {
        'Data': 'Text',
        'Long Text': 'Text', 
        'Select': 'Multi-choice',
        'Rating': 'Rating',
        'Question': 'Yes/No'
      };
      return typeMap[fieldType] || 'Text';
    }

    const startAutoSave = () => {
      if (autoSaveInterval) clearInterval(autoSaveInterval)
      autoSaveInterval = setInterval(() => {
        saveDraft(true) // Silent save
      }, 300000) // Auto-save every 5 minutes
    }

    const validateSurvey = () => {
      Object.keys(validationErrors).forEach(key => delete validationErrors[key])
      let isValid = true

      currentSurveyTemplate.value.questions.forEach(question => {
        if (question.required && (!surveyAnswers[question.name] || surveyAnswers[question.name] === '')) {
          validationErrors[question.name] = t('validationError')
          isValid = false
        }
      })

      return isValid
    }

    const saveDraft = async (silent = false) => {
      isLoading.value = !silent
      try {
        // Simulate API call to save draft
        await new Promise(resolve => setTimeout(resolve, 800))

        if (!silent) {
          showToast(t('saveSuccess'))
        }
      } catch (error) {
        if (!silent) {
          showToast('Error saving draft', 'error')
        }
      } finally {
        isLoading.value = false
      }
    }

    const submitSurvey = async () => {
      if (!validateSurvey()) {
        showToast(t('validationError'), 'error')
        return
      }

      isLoading.value = true
      try {
        // Simulate API call to submit survey
        await new Promise(resolve => setTimeout(resolve, 1500))

        showToast(t('submitSuccess'))

        // Refresh the survey responses to reflect the updated status
        await fetchSurveyResponses()

        // Reset form
        selectedOpportunity.value = null
        currentSurveyTemplate.value = null
        surveyTemplates.value = []
        selectedTemplateId.value = null
        Object.keys(surveyAnswers).forEach(key => delete surveyAnswers[key])

        if (autoSaveInterval) {
          clearInterval(autoSaveInterval)
        }

        // Switch to My Surveys tab
        activeTab.value = 'my-surveys'
      } catch (error) {
        showToast('Error submitting survey', 'error')
      } finally {
        isLoading.value = false
      }
    }

    const fetchSurveyResponses = async () => {
      isLoading.value = true
      surveyResponses.value = [] // Clear existing responses

      const fields = encodeURIComponent(JSON.stringify(['name', 'customer_name', 'opportunity_from', 'title', 'status', 'workflow_state', 'custom_surveyor', 'creation', 'modified']));
      const filters = encodeURIComponent(JSON.stringify([
        ['custom_surveyor', '=', currentUser.value.name]
      ]));

      try {
        for (const oppType of ["Opportunity", "Opportunity Hotels", "Opportunity SM", "Opportunity Tenders"]) {
          try {
            const resp = await fetch(`/api/resource/${oppType}?fields=${fields}&filters=${filters}`, {
              credentials: 'include',
            });

            if (resp.ok) {
              const data = await resp.json();
              const userOpportunities = data.data
                .filter(opp => opp.custom_surveyor === currentUser.value.name)
                .map(opp => ({
                  name: opp.name,
                  survey_template: getSurveyTemplateTitle(oppType),
                  title: opp.title,
                  doctype: oppType,
                  status: opp.workflow_state === 'Surveying' ? 'In Progress' : 'Submitted',
                  creation: opp.creation,
                  workflow_state: opp.workflow_state,
                  customer_name: opp.customer_name
                }));

              surveyResponses.value.push(...userOpportunities);
            }
          } catch (error) {
            console.error(`Error fetching ${oppType}:`, error);
          }
        }

        console.log('Fetched survey responses:', surveyResponses.value)
      } finally {
        isLoading.value = false
      }
    }

    const getSurveyTemplateTitle = (doctype) => {
      const templates = {
        'Opportunity': 'Dedicated Server Technical Assessment',
        'Opportunity Hotels': 'Hotel Management System Assessment',
        'Opportunity SM': 'Small Business Technical Assessment',
        'Opportunity Tenders': 'Tender Opportunity Assessment'
      };
      return templates[doctype] || 'Technical Assessment Survey';
    }

    const viewSurveyResponse = async (response) => {
      if (response.status === 'In Progress') {
        // If survey is in progress, allow user to continue filling it out
        isLoading.value = true
        try {
          // Fetch the full opportunity data
          const oppResponse = await fetch(`/api/resource/${response.doctype}/${response.name}`, {
            credentials: 'include'
          })
          
          if (oppResponse.ok) {
            const oppData = await oppResponse.json()
            selectedOpportunity.value = {
              name: oppData.data.name,
              title: oppData.data.title,
              doctype: response.doctype,
              customer_name: oppData.data.customer_name,
              status: oppData.data.status,
              workflow_state: oppData.data.workflow_state
            }
            
            // Load available survey templates for selection
            await fetchSurveyTemplates()
            activeTab.value = 'fill-survey'
            showToast(`Continuing survey for: ${response.title}`)
            // Note: User will need to select a template to continue
          } else {
            throw new Error('Failed to fetch opportunity data')
          }
        } catch (error) {
          showToast('Error loading survey: ' + error.message, 'error')
        } finally {
          isLoading.value = false
        }
      } else {
        // For submitted surveys, just show a message (could be extended to show survey results)
        showToast(`Viewing submitted survey for: ${response.title}`)
        // Implementation for viewing submitted survey response would go here
      }
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString(currentLanguage.value === 'ar' ? 'ar-SA' : 'en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    // Initialize field value based on type and default
    const initializeFieldValue = (field) => {
      if (field.default_value) {
        return field.default_value;
      }
      
      switch (field.field_type) {
        case 'Check':
          return false;
        case 'Int':
        case 'Float':
          return 0;
        case 'Select':
          // Return first option if available
          if (field.options) {
            const options = field.options.split('\n').filter(opt => opt.trim() !== '');
            return options.length > 0 ? options[0] : '';
          }
          return '';
        case 'Table':
          return [];
        default:
          return '';
      }
    };

    // Lifecycle hooks
    onMounted(() => {
      // Load saved language preference
      const savedLanguage = localStorage.getItem('language')
      if (savedLanguage) {
        currentLanguage.value = savedLanguage
      }

      checkLoggedIn().then(async ({ loggedIn, user }) => {

        if (loggedIn) {
          isAuthenticated.value = true
          currentUser.value = {
            name: user,
            full_name: 'Technical Assessment User',
            roles: ['Technical Assessment']
          }
          await Promise.all([fetchOpportunities(), fetchSurveyResponses()])
        } else {
          isAuthenticated.value = false
        }
      }).catch(err => {
        console.error('Error checking login status:', err)
      })
    })

    // Watch for language changes to update document direction
    watch(currentLanguage, (newLang) => {
      document.documentElement.dir = newLang === 'ar' ? 'rtl' : 'ltr'
      document.documentElement.lang = newLang
    })

    return {
      // State
      isLoading,
      isAuthenticated,
      currentUser,
      activeTab,
      currentLanguage,
      toast,
      loginForm,
      opportunities,
      selectedOpportunity,
      currentSurveyTemplate,
      surveyTemplates,
      selectedTemplateId,
      surveyAnswers,
      validationErrors,
      opportunitySearch,
      surveyResponses,
      filters,

      // Computed
      filteredOpportunities,
      surveyProgress,
      filteredSurveyResponses,

      // Methods
      t,
      toggleLanguage,
      login,
      logout,
      selectOpportunity,
      selectSurveyTemplate,
      fetchSurveyTemplates,
      initializeFieldValue,
      mapFieldTypeToQuestionType,
      saveDraft,
      submitSurvey,
      viewSurveyResponse,
      formatDate,
      fetchOpportunities,
      fetchSurveyResponses,
      getSurveyTemplateTitle
    }
  }
}
</script>

<style>
@import 'tailwindcss';

.rtl {
  direction: rtl;
}

.rtl .space-x-4>*+* {
  margin-left: 0;
  margin-right: 1rem;
}

.rtl .space-x-2>*+* {
  margin-left: 0;
  margin-right: 0.5rem;
}

.rtl .space-x-3>*+* {
  margin-left: 0;
  margin-right: 0.75rem;
}

.rtl .space-x-8>*+* {
  margin-left: 0;
  margin-right: 2rem;
}

/* Custom animations */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in {
  animation: fadeIn 0.3s ease-out;
}

/* Responsive design improvements */
@media (max-width: 768px) {
  .grid-cols-1.md\:grid-cols-4 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }

  .space-x-4>*+* {
    margin-left: 0;
    margin-top: 1rem;
  }

  .flex {
    flex-direction: column;
  }

  .justify-between {
    justify-content: flex-start;
  }
}

/* Focus styles for accessibility */
button:focus,
input:focus,
select:focus,
textarea:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Loading spinner */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* Smooth transitions */
* {
  transition-property: color, background-color, border-color, text-decoration-color, fill, stroke, opacity, box-shadow, transform, filter, backdrop-filter;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Enhanced button hover effects */
button:hover {
  transform: translateY(-1px);
}

button:active {
  transform: translateY(0);
}

/* Card hover effects */
.hover\:shadow-md:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

/* Progress bar animation */
.bg-gradient-to-r {
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }

  100% {
    background-position: 200% 0;
  }
}
</style>